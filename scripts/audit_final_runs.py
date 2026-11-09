"""Independently check frozen artifacts, references, energies and tokenizer budgets."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np

from qrag.data import load_examples
from qrag.datasets import score_answer, score_evidence
from qrag.evaluation import latest_records
from qrag.experiments.artifacts import file_hash, value_hash, write_json


def main():
    from transformers import AutoTokenizer

    matrix = json.loads(Path("configs/final_matrix.json").read_text())
    tokenizers = {}
    report = {
        "execution_cycle": matrix["execution_cycle"],
        "runs": {},
        "total_latest_records": 0,
    }
    source_hashes = set()
    additional = []
    for name in ["formulation_controls", "preparation_control"]:
        additional.extend(
            json.loads(Path(f"configs/{name}.json").read_text())["configs"]
        )
    for entry in matrix["configs"] + additional:
        config_path = Path(entry["config"])
        assert file_hash(config_path) == entry["sha256"]
        spec = json.loads(config_path.read_text())
        run = Path("results") / config_path.stem
        manifest = json.loads((run / "manifest.json").read_text())
        assert manifest["status"] in {"completed", "completed_with_errors"}, run
        assert manifest["identity"]["spec"] == spec
        assert file_hash(Path(spec["model"]["dataset"])) == spec["dataset_sha256"]
        snapshot = json.loads((run / "source_snapshot.json").read_text())
        digest = value_hash(
            {
                name: hashlib.sha256(text.encode()).hexdigest()
                for name, text in snapshot.items()
            }
        )
        if config_path.stem.endswith("_prepared"):
            extension = json.loads((run / "extension_snapshot.json").read_text())
            assert (
                hashlib.sha256(extension["extension_source"].encode()).hexdigest()
                == extension["extension_sha256"]
            )
            assert extension["frozen_core_sha256"] == digest
            composite = value_hash(
                {
                    "frozen_core_sha256": digest,
                    "extension_sha256": extension["extension_sha256"],
                }
            )
            assert (
                composite
                == extension["combined_sha256"]
                == manifest["identity"]["source_sha256"]
            )
        else:
            assert digest == manifest["identity"]["source_sha256"]
        source_hashes.add(digest)
        examples = {
            q.id: (q, labels)
            for q, labels in load_examples(Path(spec["model"]["dataset"]))[
                : spec["model"]["limit"]
            ]
        }
        rows = latest_records(run / "predictions.jsonl")
        expected = {(q, m["name"]) for q in examples for m in spec["methods"]}
        assert {(r["question_id"], r["method"]) for r in rows} == expected
        key = (spec["model"]["generator_model"], spec["model"]["generator_revision"])
        if key not in tokenizers:
            tokenizers[key] = AutoTokenizer.from_pretrained(
                key[0], revision=key[1], local_files_only=True
            )
        tokenizer = tokenizers[key]
        checked_contexts = {}
        success = 0
        failures = []
        limit_hits = 0
        for row in rows:
            if row["status"] != "success":
                failures.append(
                    {
                        "question_id": row["question_id"],
                        "method": row["method"],
                        "type": row["error_type"],
                        "error": row["error"],
                    }
                )
                continue
            query, labels = examples[row["question_id"]]
            lookup = {d.id: d for d in query.documents}
            assert len(row["candidate_ids"]) == len(set(row["candidate_ids"]))
            assert set(row["candidate_ids"]) <= set(lookup)
            indices = row["selection"]["indices"]
            ids = [row["candidate_ids"][i] for i in indices]
            assert (
                ids == row["selected_ids"]
                and len(ids) == len(set(ids)) == row["selected_count"]
            )
            if spec.get("budget_mode", "count") == "count":
                assert len(ids) == min(spec["model"]["k"], len(row["candidate_ids"]))
            else:
                assert 0 < len(ids) and row["context_tokens"] <= spec["context_budget"]
                assert row["estimated_token_cost"] <= spec["context_budget"]
            selected = tuple(lookup[i] for i in ids)
            expected_metrics = {
                **score_answer(row["answer"], labels),
                **score_evidence(selected, labels),
            }
            for metric, value in expected_metrics.items():
                actual = row["metrics"][metric]
                assert (value is None and actual is None) or (
                    value is not None and abs(actual - value) < 1e-10
                ), (run, metric)
            linear = np.array(row["linear_coefficients"])
            pairs = np.array(row["pair_coefficients"])
            sparse = np.array(row["surrogate_pairs"])
            assert not np.any(np.tril(pairs)) and not np.any(np.tril(sparse))
            energy = sum(linear[i] for i in indices) + sum(
                pairs[i, j] for i, j in combinations(indices, 2)
            )
            surrogate = sum(linear[i] for i in indices) + sum(
                sparse[i, j] for i, j in combinations(indices, 2)
            )
            assert (
                abs(energy - row["full_energy"]) < 1e-7
                and abs(surrogate - row["surrogate_energy"]) < 1e-7
            )
            assert abs(row["selection"]["energy"] - surrogate) < 1e-7
            if row["selection"]["optimal"]:
                assert row["selection"]["status"] == "optimal"
                bound = row["selection"]["lower_bound"]
                if bound is not None:
                    assert abs(bound - surrogate) < 1e-5
            if row.get("sparsification"):
                info = row["sparsification"]
                assert np.count_nonzero(sparse) == info["retained_edges"]
                assert abs(np.abs(pairs - sparse).sum() - info["removed_l1"]) < 1e-7
            resource = row.get("resources", {})
            if resource.get("hardware") is False:
                assert sum(resource["sampled_counts"].values()) == resource["shots"]
                assert 0 <= resource["feasible_shots"] <= resource["shots"]
                if (
                    resource["mixer"] == "xy"
                    and not resource["noise_two_qubit_depolarizing_probability"]
                ):
                    assert abs(resource["feasible_fraction"] - 1) < 1e-12
            context_key = (query.id, tuple(ids))
            if context_key not in checked_contexts:
                encoded = tokenizer.encode(row["prompt"], add_special_tokens=False)
                assert encoded == row["input_ids"]
                context = "\n\n".join(
                    f"[Source {d.id}: {d.title}]\n{d.text}" for d in selected
                )
                assert (
                    len(tokenizer.encode(context, add_special_tokens=False))
                    == row["context_tokens"]
                )
                checked_contexts[context_key] = (row["prompt"], row["answer"])
            else:
                assert checked_contexts[context_key] == (row["prompt"], row["answer"])
            assert row["input_tokens"] == len(row["input_ids"])
            assert (
                row["input_tokens"] + spec["model"]["max_new_tokens"]
                <= spec["model"]["max_input_tokens"]
            )
            assert row["output_tokens"] <= spec["model"]["max_new_tokens"]
            limit_hits += int(row.get("hit_output_limit", False))
            success += 1
        report["runs"][run.name] = {
            "records": len(rows),
            "successful": success,
            "failures": failures,
            "output_limit_hits": limit_hits,
            "distinct_contexts_retokenized": len(checked_contexts),
            "source_sha256": digest,
            "checks": [
                "frozen config/data/source hashes",
                "complete question/method grid",
                "selection IDs and budgets",
                "dataset-specific answer/evidence metrics",
                "independent pair-sum energies",
                "sparse edge counts and removed mass",
                "solver certification",
                "shot counts and ideal XY feasibility",
                "exact prompt IDs and assembled context tokens",
            ],
        }
        report["total_latest_records"] += len(rows)
        print(
            "Audited",
            run.name,
            len(rows),
            "records; failures",
            len(failures),
            flush=True,
        )
    assert len(source_hashes) == 1, (
        "Definitive primary runs do not share one scientific source fingerprint"
    )
    report["common_source_sha256"] = next(iter(source_hashes))
    write_json(Path("docs/research_report/evidence/final_audit.json"), report)


if __name__ == "__main__":
    main()
