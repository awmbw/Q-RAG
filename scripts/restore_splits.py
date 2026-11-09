"""Reconstruct frozen files by manifest IDs and verify their exact hashes."""

import argparse
import json
import zipfile
from pathlib import Path

from qrag.datasets import hotpot_record, musique_record
from qrag.experiments.artifacts import file_hash, write_json


def main():
    from datasets import load_dataset

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path("configs/splits/research_v1.json")
    )
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    archive = Path("data/raw/musique_v1.0.zip")
    if not archive.exists():
        import gdown

        archive.parent.mkdir(parents=True, exist_ok=True)
        gdown.download(
            id="1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h", output=str(archive), quiet=False
        )
    if file_hash(archive) != manifest["musique_zip_sha256"]:
        raise ValueError("Official MuSiQue archive changed")
    hotpot = load_dataset(
        "hotpotqa/hotpot_qa", "distractor", revision=manifest["hotpot_revision"]
    )
    for dataset, entry in manifest["datasets"].items():
        for split, metadata in entry["splits"].items():
            target = args.output_root / metadata["path"]
            if target.exists():
                if file_hash(target) != metadata["sha256"]:
                    raise ValueError(f"Existing file differs: {target}")
                continue
            wanted = set(metadata["ids"])
            if dataset == "hotpotqa":
                source = hotpot["train" if split == "development" else "validation"]
                records = {
                    r["id"]: hotpot_record(r) for r in source if r["id"] in wanted
                }
            else:
                with zipfile.ZipFile(archive) as zipped:
                    name = "train" if split == "development" else "dev"
                    members = [
                        p
                        for p in zipped.namelist()
                        if p.endswith(f"musique_ans_v1.0_{name}.jsonl")
                        and not p.startswith("__MACOSX")
                    ]
                    if len(members) != 1:
                        raise ValueError("Ambiguous archive")
                    records = {}
                    for line in zipped.read(members[0]).decode().splitlines():
                        raw = json.loads(line)
                        if raw["id"] in wanted:
                            records[raw["id"]] = musique_record(raw)
            if set(records) != wanted:
                raise ValueError("Frozen source IDs missing")
            write_json(target, [records[q] for q in metadata["ids"]])
            if file_hash(target) != metadata["sha256"]:
                raise ValueError("Reconstructed data hash differs")
            print("Verified", target, flush=True)


if __name__ == "__main__":
    main()
