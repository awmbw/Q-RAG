"""Supplementary exact compiled-gate-cap experiment; no primary-run retuning."""

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

import numpy as np

from qrag.config import ExperimentConfig
from qrag.data import load_examples
from qrag.datasets import score_answer, score_evidence
from qrag.evaluation import latest_records
from qrag.experiments.artifacts import file_hash, source_hash, utc_now, write_json
from qrag.experiments.journal import JournalRunStore
from qrag.models import LocalModels
from qrag.optimization import SelectionProblem
from qrag.quantum import compilation_resources, qaoa_circuit, solve_qaoa
from qrag.sparsification import sparsify


def choose_capped(problem, comp, rule, seed, cap, mixer="xy"):
    started = perf_counter()
    trials = []
    for fraction in np.linspace(1.0, 0.0, 21):
        sparse, meta = sparsify(problem, comp, rule, float(fraction), seed)
        circuit, _ = qaoa_circuit(sparse, [0.37, 0.61], p=1, mixer=mixer, seed=seed)
        gates = compilation_resources(circuit, seed)["line"]["two_qubit_gates"]
        trials.append({"fraction": float(fraction), "line_two_qubit_gates": gates})
        if gates <= cap:
            return (
                sparse,
                meta,
                {
                    "gate_cap": cap,
                    "prefix_trials": trials,
                    "gate_budget_preprocess_seconds": perf_counter() - started,
                },
            )
    return (
        None,
        None,
        {
            "gate_cap": cap,
            "prefix_trials": trials,
            "gate_budget_preprocess_seconds": perf_counter() - started,
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/gate_budget_supplement.json")
    )
    args = parser.parse_args()
    spec = json.loads(args.config.read_text())
    for dataset in spec["datasets"]:
        primary = Path("results") / f"final_{dataset}_quantum"
        manifest = json.loads((primary / "manifest.json").read_text())
        if manifest["status"] not in {"completed", "completed_with_errors"}:
            raise ValueError("Primary run unfinished")
        base = {
            r["question_id"]: r
            for r in latest_records(primary / "predictions.jsonl")
            if r["method"] == "milp_full" and r["status"] == "success"
        }
        ids = manifest["identity"]["question_ids"][: spec["questions_per_dataset"]]
        config = replace(
            ExperimentConfig(**manifest["identity"]["spec"]["model"]), limit=len(ids)
        )
        original = {
            q.id: (q, labels) for q, labels in load_examples(Path(config.dataset))
        }
        methods = [
            {
                "name": f"gate_{rule}_s{seed}",
                "rule": rule,
                "seed": seed,
                "solver": "qaoa",
            }
            for rule in ["absolute", "evidence"]
            for seed in spec["seeds"]
        ]
        methods.append(
            {
                "name": "gate_penalty_control",
                "rule": "absolute",
                "seed": 42,
                "solver": "qaoa",
                "mixer": "penalty",
            }
        )
        output = Path("results") / f"final_{dataset}_gatecap"
        identity = {
            "spec": {**spec, "model": config.as_dict(), "methods": methods},
            "question_ids": ids,
            "source_sha256": source_hash(),
            "driver_sha256": file_hash(Path(__file__)),
            "primary_predictions_sha256": file_hash(primary / "predictions.jsonl"),
        }
        store = JournalRunStore(output, identity, output.exists())
        store.manifest["status"] = "running"
        invocation = {"started_at": utc_now()}
        store.manifest["invocations"].append(invocation)
        started = perf_counter()
        write_json(
            output / "source_snapshot.json",
            {
                "driver": Path(__file__).read_text(),
                "qrag_source": json.loads(
                    (primary / "source_snapshot.json").read_text()
                ),
            },
        )
        model = LocalModels(config)
        invocation["preparation"] = model.prepare()
        store.save_manifest()
        try:
            for qid in ids:
                source = base[qid]
                query, labels = original[qid]
                documents = {d.id: d for d in query.documents}
                query = replace(
                    query,
                    documents=tuple(documents[i] for i in source["candidate_ids"]),
                )
                problem = SelectionProblem(
                    np.array(source["linear_coefficients"]),
                    np.array(source["pair_coefficients"]),
                    min(config.k, len(query.documents)),
                )
                positions = {d.id: i for i, d in enumerate(query.documents)}
                comp = np.zeros_like(problem.pairs)
                for edge in source["graph"]["edges"]:
                    i, j = positions[edge["source"]], positions[edge["target"]]
                    comp[i, j] = comp[j, i] = edge["weight"]
                generations = {}
                for method in methods:
                    key = (qid, method["name"])
                    if (
                        key in store.records
                        and store.records[key]["status"] == "success"
                    ):
                        continue
                    row = {
                        "question_id": qid,
                        "method": method["name"],
                        "status": "error",
                        "candidate_ids": source["candidate_ids"],
                    }
                    try:
                        sparse, meta, preprocess = choose_capped(
                            problem,
                            comp,
                            method["rule"],
                            method["seed"],
                            spec["line_gate_cap"],
                            method.get("mixer", "xy"),
                        )
                        row["resources"] = preprocess
                        if sparse is None:
                            raise ValueError(
                                "No tested retention level meets complete compiled-gate cap"
                            )
                        result, resources = solve_qaoa(
                            sparse,
                            p=1,
                            seed=method["seed"],
                            shots=spec["shots"],
                            max_evals=spec["max_evals"],
                            mixer=method.get("mixer", "xy"),
                        )
                        row["resources"] = {**resources, **preprocess}
                        if resources["line"]["two_qubit_gates"] > spec["line_gate_cap"]:
                            raise ValueError(
                                "Final optimized compilation exceeds the cap; no silent backoff"
                            )
                        if result.indices is None:
                            raise ValueError("No feasible measured context")
                        selected = tuple(query.documents[i] for i in result.indices)
                        reused = result.indices in generations
                        if not reused:
                            generations[result.indices] = model.generate(
                                query, selected
                            )
                        generation = generations[result.indices]
                        row.update(generation)
                        row.update(
                            {
                                "status": "success",
                                "selection": asdict(result),
                                "selection_seconds": result.seconds,
                                "generation_reused": reused,
                                "actual_generation_seconds": 0.0
                                if reused
                                else generation["generation_seconds"],
                                "selected_ids": [d.id for d in selected],
                                "selected_titles": [d.title for d in selected],
                                "selected_count": len(selected),
                                "full_energy": problem.energy(result.indices),
                                "surrogate_energy": sparse.energy(result.indices),
                                "sparsification": meta,
                                "feasible": True,
                                "budget_mode": "count_and_complete_compiled_line_gate_cap",
                                "metrics": {
                                    **score_answer(generation["answer"], labels),
                                    **score_evidence(selected, labels),
                                },
                            }
                        )
                    except Exception as exc:
                        row.update(
                            {"error_type": type(exc).__name__, "error": str(exc)}
                        )
                    store.save_record(row)
                print(dataset, qid, "gate-cap records saved", flush=True)
            from qrag.experiments.study import summarize

            write_json(output / "summary.json", summarize(list(store.records.values())))
            store.manifest["status"] = (
                "completed_with_errors"
                if any(r["status"] != "success" for r in store.records.values())
                else "completed"
            )
        finally:
            invocation.update(
                {"ended_at": utc_now(), "wall_seconds": perf_counter() - started}
            )
            store.save_manifest()


if __name__ == "__main__":
    main()
