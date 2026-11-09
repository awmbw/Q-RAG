"""Separate best-of-samples coverage from the trained circuit's distribution."""

import json
from pathlib import Path
from time import perf_counter

import numpy as np

from qrag.evaluation import latest_records
from qrag.experiments.artifacts import file_hash, source_hash, write_json
from qrag.optimization import SelectionProblem
from qrag.quantum import diagonal_energies, qaoa_circuit, solve_qaoa


def at_least_once(probability, draws):
    if probability >= 1:
        return 1.0
    return float(-np.expm1(draws * np.log1p(-max(0.0, probability))))


def expected_best(energies, probabilities, draws):
    order = np.argsort(energies, kind="stable")
    energies = energies[order]
    probabilities = probabilities[order]
    cumulative = np.clip(np.cumsum(probabilities), 0, 1)
    previous = np.r_[0, cumulative[:-1]]
    mass = np.power(1 - previous, draws) - np.power(1 - cumulative, draws)
    success = at_least_once(float(cumulative[-1]), draws)
    return float(energies @ mass / success) if success else None


def main():
    from qiskit.quantum_info import Statevector

    spec_path = Path("configs/sampling_coverage.json")
    spec = json.loads(spec_path.read_text())
    source = Path(spec["source_run"]) / "predictions.jsonl"
    selected = [
        r
        for r in latest_records(source)
        if r["method"] == spec["source_method"] and r["status"] == "success"
    ][: spec["questions"]]
    out = Path("results/sampling_coverage")
    out.mkdir(parents=True, exist_ok=False)
    identity = {
        "spec": spec,
        "source_predictions_sha256": file_hash(source),
        "driver_sha256": file_hash(Path(__file__)),
        "scientific_source_sha256": source_hash(),
    }
    write_json(out / "manifest.json", identity)
    records = []
    instances = []
    started = perf_counter()
    for row in selected:
        original_a = np.array(row["linear_coefficients"])
        original_b = np.array(row["pair_coefficients"])
        for n in spec["candidate_sizes"]:
            order = sorted(np.argsort(original_a, kind="stable")[:n].tolist())
            if len(order) != n:
                raise ValueError("Insufficient genuine candidates")
            problem = SelectionProblem(
                original_a[order], original_b[np.ix_(order, order)], spec["k"]
            )
            energies, bits = diagonal_energies(problem.linear, problem.pairs)
            feasible = bits.sum(axis=1) == problem.k
            values = energies[feasible]
            optimum = float(values.min())
            optimal = feasible & (energies <= optimum + 1e-9)
            uniform_optimum = float(optimal.sum() / feasible.sum())
            instances.append(
                {
                    "question_id": row["question_id"],
                    "n": n,
                    "candidate_ids": [row["candidate_ids"][i] for i in order],
                    "linear": problem.linear.tolist(),
                    "pairs": problem.pairs.tolist(),
                    "feasible_subsets": int(feasible.sum()),
                    "optimum": optimum,
                }
            )
            uniform = np.full(len(values), 1 / len(values))
            for mixer in spec["mixers"]:
                for seed in spec["seeds"]:
                    result, resources = solve_qaoa(
                        problem,
                        p=spec["p"],
                        mixer=mixer,
                        seed=seed,
                        max_evals=spec["max_evals"],
                        shots=1024,
                    )
                    circuit, _ = qaoa_circuit(
                        problem, resources["angles"], spec["p"], mixer, seed
                    )
                    probabilities = Statevector(circuit).probabilities()
                    # Statevector normalization can differ from one by roundoff.
                    p_optimum = float(np.clip(probabilities[optimal].sum(), 0, 1))
                    p_feasible = float(np.clip(probabilities[feasible].sum(), 0, 1))
                    budgets = []
                    for draws in spec["sample_budgets"]:
                        qbest = expected_best(values, probabilities[feasible], draws)
                        ubest = expected_best(values, uniform, draws)
                        budgets.append(
                            {
                                "samples": draws,
                                "uniform_optimum_probability": at_least_once(
                                    uniform_optimum, draws
                                ),
                                "qaoa_optimum_probability": at_least_once(
                                    p_optimum, draws
                                ),
                                "qaoa_no_feasible_probability": float(
                                    (1 - p_feasible) ** draws
                                ),
                                "uniform_expected_gap": ubest - optimum,
                                "qaoa_expected_gap_given_feasible": qbest - optimum
                                if qbest is not None
                                else None,
                            }
                        )
                    record = {
                        "question_id": row["question_id"],
                        "n": n,
                        "k": problem.k,
                        "mixer": mixer,
                        "seed": seed,
                        "feasible_subsets": int(feasible.sum()),
                        "single_draw_optimum_probability": p_optimum,
                        "single_draw_feasible_probability": p_feasible,
                        "solver_seconds": result.seconds,
                        "angles": resources["angles"],
                        "line_two_qubit_gates": resources["line"]["two_qubit_gates"],
                        "evaluations": resources["evaluations"],
                        "budgets": budgets,
                    }
                    records.append(record)
                    with (out / "records.jsonl").open("a") as handle:
                        handle.write(json.dumps(record, sort_keys=True) + "\n")
            print(row["question_id"], "n", n, "sampling coverage saved", flush=True)
    write_json(
        out / "summary.json",
        {"records": len(records), "wall_seconds": perf_counter() - started},
    )
    write_json(
        Path("docs/research_report/evidence/sampling_coverage.json"),
        {
            **identity,
            "records": records,
            "instances": instances,
            "wall_seconds": perf_counter() - started,
            "note": "Exact distribution calculations conditional on the recorded development instances. No labels or LLM answers enter this study. Exact-expectation angle training is simulation-only.",
        },
    )


if __name__ == "__main__":
    main()
