"""Regenerate statistics from compact published predictions, with no models/data."""

import argparse
import gzip
import json
import math
from pathlib import Path

from resource_summary import add_circuit_summaries

from qrag.evaluation import analyze
from qrag.experiments.artifacts import file_hash, write_json


def equivalent(actual, expected):
    """Permit only floating-point reduction roundoff across machines."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            equivalent(actual[key], expected[key]) for key in actual
        )
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            equivalent(a, b) for a, b in zip(actual, expected)
        )
    if isinstance(actual, float) or isinstance(expected, float):
        return (
            isinstance(actual, (float, int))
            and isinstance(expected, (float, int))
            and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
        )
    return actual == expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence", type=Path, default=Path("docs/research_report/evidence")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/public_table_reproduction")
    )
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    count = 0
    for metadata_path in sorted(args.evidence.glob("final_*.json")):
        metadata = json.loads(metadata_path.read_text())
        if "compact_predictions_file" not in metadata:
            continue
        predictions = args.evidence / metadata["compact_predictions_file"]
        if file_hash(predictions) != metadata["compact_predictions_sha256"]:
            raise ValueError("Public prediction hash mismatch")
        data = (
            gzip.decompress(predictions.read_bytes())
            if predictions.suffix == ".gz"
            else predictions.read_bytes()
        )
        rows = [json.loads(line) for line in data.decode().splitlines()]
        reference = (
            "gate_absolute" if metadata_path.stem.endswith("_gatecap") else "milp_full"
        )
        result = analyze(rows, reference)
        add_circuit_summaries(result, rows)
        if args.verify:
            recorded = json.loads(
                (
                    Path("paper/results") / (metadata_path.stem + "_analysis.json")
                ).read_text()
            )
            assert equivalent(result["table"], recorded["table"])
            assert equivalent(
                result["paired_differences_to_reference"],
                recorded["paired_differences_to_reference"],
            )
        write_json(args.output / (metadata_path.stem + ".json"), result)
        count += 1
    if not count:
        raise ValueError("No completed public final evidence files found")
    print(
        "Reproduced",
        count,
        "public result tables and paired intervals without neural inference",
    )


if __name__ == "__main__":
    main()
