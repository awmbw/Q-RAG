"""Release frozen inference coefficient arrays for model-free solver experiments."""

import gzip
import json
from pathlib import Path

import numpy as np

from qrag.evaluation import latest_records
from qrag.experiments.artifacts import file_hash, write_json


def main():
    instances = []
    source_hashes = set()
    for stem in [
        "final_hotpotqa_quantum",
        "final_musique_quantum",
        "final_musique_quantum12",
        "final_musique_quantum16",
    ]:
        root = Path("results") / stem
        manifest = json.loads((root / "manifest.json").read_text())
        assert manifest["status"] in {"completed", "completed_with_errors"}
        source_hashes.add(manifest["identity"]["source_sha256"])
        rows = latest_records(root / "predictions.jsonl")
        prediction_hash = file_hash(root / "predictions.jsonl")
        for row in rows:
            if row["method"] != "milp_full":
                continue
            assert row["status"] == "success"
            comp = np.zeros_like(row["pair_coefficients"])
            positions = {key: i for i, key in enumerate(row["candidate_ids"])}
            for edge in row["graph"]["edges"]:
                i, j = positions[edge["source"]], positions[edge["target"]]
                comp[i, j] = comp[j, i] = edge["weight"]
            instances.append(
                {
                    "run": stem,
                    "question_id": row["question_id"],
                    "candidate_ids": row["candidate_ids"],
                    "linear": row["linear_coefficients"],
                    "pairs": row["pair_coefficients"],
                    "complementarity": comp.tolist(),
                    "k": len(row["selection"]["indices"]),
                    "reference_optimum": {
                        "energy": row["full_energy"],
                        "indices": row["selection"]["indices"],
                        "certified": row["selection"]["optimal"],
                    },
                    "source_predictions_sha256": prediction_hash,
                }
            )
    assert len(source_hashes) == 1 and len(instances) == 110
    output = Path("docs/research_report/evidence")
    target = output / "quantum_instances.json.gz"
    payload = {
        "scope": "110 frozen optimization instances from 100 unique held-out questions; nested 12/16 sensitivities reuse five MuSiQue IDs. No source text, answer references or supporting annotations. Reference optima are evaluation-only solver outputs.",
        "source_sha256": next(iter(source_hashes)),
        "instances": instances,
    }
    target.write_bytes(
        gzip.compress(
            json.dumps(payload, sort_keys=True, allow_nan=False).encode(), mtime=0
        )
    )
    write_json(
        output / "quantum_instances_manifest.json",
        {
            "file": target.name,
            "sha256": file_hash(target),
            "instances": len(instances),
            "source_sha256": next(iter(source_hashes)),
        },
    )
    snapshot = Path("results/final_hotpotqa_quantum/source_snapshot.json")
    (output / "scientific_source_snapshot.json").write_bytes(snapshot.read_bytes())
    write_json(
        output / "preparation_extension_snapshots.json",
        {
            dataset: json.loads(
                Path(
                    f"results/final_{dataset}_prepared/extension_snapshot.json"
                ).read_text()
            )
            for dataset in ["hotpotqa", "musique"]
        },
    )
    print(
        "Exported 110 frozen optimization instances and exact scientific source snapshots"
    )


if __name__ == "__main__":
    main()
