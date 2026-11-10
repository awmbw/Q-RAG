"""Run a frozen quantum selection instance without datasets, embeddings or an LLM."""

import argparse
import gzip
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from qrag.experiments.artifacts import file_hash, source_hash, write_json
from qrag.optimization import SelectionProblem, select_milp
from qrag.quantum import solve_qaoa
from qrag.sparsification import sparsify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default="final_hotpotqa_quantum")
    parser.add_argument("--question-id")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--p", type=int, default=1)
    parser.add_argument(
        "--sparsifier", choices=["absolute", "random", "degree", "evidence"]
    )
    parser.add_argument("--prepared", action="store_true")
    parser.add_argument("--verify-recorded", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/quantum_instance_reproduction.json"),
    )
    args = parser.parse_args()
    if args.verify_recorded and (
        args.seed not in {41, 42, 43} or (args.sparsifier and args.p != 1)
    ):
        parser.error(
            "Recorded comparisons require seed 41/42/43 and p=1 for sparse circuits"
        )
    root = Path("docs/research_report/evidence")
    metadata = json.loads((root / "quantum_instances_manifest.json").read_text())
    archive = root / metadata["file"]
    assert file_hash(archive) == metadata["sha256"]
    data = json.loads(gzip.decompress(archive.read_bytes()))
    assert source_hash() == data["source_sha256"], (
        "Use the frozen scientific source for this reproduction"
    )
    row = next(
        r
        for r in data["instances"]
        if r["run"] == args.run
        and (args.question_id is None or r["question_id"] == args.question_id)
    )
    full = SelectionProblem(np.array(row["linear"]), np.array(row["pairs"]), row["k"])
    problem, sparsification = (
        sparsify(
            full, np.array(row["complementarity"]), args.sparsifier, 0.5, args.seed
        )
        if args.sparsifier
        else (full, {})
    )
    if args.prepared:
        from prepared_qaoa_study import prepared_circuit

        import qrag.quantum as quantum

        quantum.qaoa_circuit = prepared_circuit
    selection, resources = solve_qaoa(problem, p=args.p, seed=args.seed)
    exact = select_milp(full)
    result = {
        "instance": row["question_id"],
        "run": args.run,
        "prepared": args.prepared,
        "selection": asdict(selection),
        "resources": resources,
        "sparsification": sparsification,
        "full_energy": full.energy(selection.indices)
        if selection.indices is not None
        else None,
        "exact_reference": asdict(exact),
    }
    if args.verify_recorded:
        stem = args.run.replace("_quantum", "_prepared") if args.prepared else args.run
        evidence = json.loads((root / (stem + ".json")).read_text())
        path = root / evidence["compact_predictions_file"]
        assert file_hash(path) == evidence["compact_predictions_sha256"]
        prefix = "prepared" if args.prepared else "xy"
        method = (
            f"{prefix}_{args.sparsifier}_f0.5"
            if args.sparsifier
            else f"{prefix}_full_p{args.p}"
        ) + f"_s{args.seed}"
        expected = next(
            r
            for r in (
                json.loads(line)
                for line in gzip.decompress(path.read_bytes()).decode().splitlines()
            )
            if r["question_id"] == row["question_id"] and r["method"] == method
        )
        assert expected["selection"]["indices"] == list(selection.indices)
        assert abs(expected["full_energy"] - result["full_energy"]) < 1e-9
        assert (
            expected["resources"]["line"]["two_qubit_gates"]
            == resources["line"]["two_qubit_gates"]
        )
        result["recorded_selection_energy_and_compilation_match"] = True
    write_json(args.output, result)
    print(
        "Reproduced",
        row["question_id"],
        "with",
        len(full.linear),
        "candidates; no model or dataset required",
    )


if __name__ == "__main__":
    main()
