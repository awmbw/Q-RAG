"""Export compact reviewable predictions and metadata without full dataset passages."""

import argparse
import json
from pathlib import Path

from qrag.experiments.artifacts import atomic_text, file_hash, write_json


def export(run, output):
    manifest = json.loads((run / "manifest.json").read_text())
    summary = json.loads((run / "summary.json").read_text())
    attempts = [
        json.loads(line)
        for line in (run / "predictions.jsonl").read_text().splitlines()
    ]
    latest = {(r["question_id"], r["method"]): r for r in attempts}
    rows = list(latest.values())
    keys = {
        "question_id",
        "method",
        "status",
        "error_type",
        "error",
        "selected_ids",
        "selected_titles",
        "selected_count",
        "answer",
        "metrics",
        "context_tokens",
        "input_tokens",
        "output_tokens",
        "full_energy",
        "surrogate_energy",
        "selection_seconds",
        "generation_seconds",
        "actual_generation_seconds",
        "generation_reused",
        "feasible",
        "budget_mode",
        "estimated_token_cost",
        "resources",
        "sparsification",
        "attempt",
        "candidate_metrics",
        "gpu_peak_allocated_bytes",
        "process_peak_rss_bytes",
    }
    compact = []
    for row in rows:
        result = {k: v for k, v in row.items() if k in keys}
        if result.get("resources"):
            result["resources"] = {
                k: v
                for k, v in result["resources"].items()
                if k not in {"sampled_counts", "training_energies"}
            }
        if "selection" in row:
            result["selection"] = {
                k: v for k, v in row["selection"].items() if k not in {"message"}
            }
        compact.append(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    predictions = output.with_suffix(".jsonl")
    atomic_text(
        predictions,
        "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in compact),
    )
    write_json(
        output,
        {
            "run_id": run.name,
            "identity": manifest["identity"],
            "git": manifest["git"],
            "status": manifest["status"],
            "invocations": manifest["invocations"],
            "summary": summary,
            "total_attempts": len(attempts),
            "compact_predictions_file": predictions.name,
            "compact_predictions_sha256": file_hash(predictions),
            "original_hashes": {
                name: file_hash(run / name)
                for name in [
                    "manifest.json",
                    "summary.json",
                    "predictions.jsonl",
                    "source_snapshot.json",
                ]
            },
            "note": "Derived compact evidence. Original artifacts and exact prompts remain in the local run bundle; hashes identify their unchanged bytes.",
        },
    )
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print("Exported", export(args.run, args.output), "records")
