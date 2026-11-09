"""Restore frozen corpus candidate files from public IDs, without rerunning retrieval."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from qrag.corpus import corpus_id, deduplicate
from qrag.data import load_examples
from qrag.experiments.artifacts import file_hash, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()
    manifest = json.loads(Path("configs/splits/corpus_v1.json").read_text())
    for dataset, entry in manifest["datasets"].items():
        paths = [
            Path(f"data/processed/research/{dataset}_{split}.json")
            for split in ["development", "evaluation"]
        ]
        for path in paths:
            assert file_hash(path) == entry["inputs"][str(path)]
        documents = deduplicate(
            [
                d
                for path in paths
                for query, _ in load_examples(path)
                for d in query.documents
            ]
        )
        lookup = {d.id: d for d in documents}
        original = json.loads(paths[1].read_text())[:100]
        for size, metadata in entry["candidate_files"].items():
            target = args.output_root / metadata["path"]
            if target.exists():
                if file_hash(target) != metadata["sha256"]:
                    raise ValueError("Existing corpus candidate file differs")
                continue
            rows = []
            for raw, profile in zip(original, entry["retrieval_profiles"], strict=True):
                support = [
                    corpus_id(d["title"], d["text"])
                    for i, d in enumerate(raw["documents"])
                    if f"{raw['id']}:d{i}" in raw.get("supporting_ids", [])
                ]
                selected = [
                    lookup[key] for key in profile["candidate_ids"][: int(size)]
                ]
                rows.append(
                    {
                        **raw,
                        "candidate_source": "retrieved",
                        "documents": [asdict(d) for d in selected],
                        "supporting_ids": support,
                        "retrieval": profile,
                    }
                )
            write_json(target, rows)
            if file_hash(target) != metadata["sha256"]:
                raise ValueError("Reconstructed corpus candidate hash differs")
            print("Verified", target, flush=True)


if __name__ == "__main__":
    main()
