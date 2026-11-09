"""Prepare frozen subsets from primary HotpotQA data and the official MuSiQue zip."""

import argparse
import json
import random
import zipfile
from pathlib import Path

from qrag.datasets import (
    duplicate_audit,
    hotpot_record,
    musique_record,
    question_key,
    validate_records,
)
from qrag.experiments.artifacts import file_hash, write_json


def choose(rows, adapter, count, excluded):
    rng = random.Random(20261110)
    order = list(range(len(rows)))
    rng.shuffle(order)
    selected, rejected = [], []
    for index in order:
        raw = rows[index]
        if raw["id"] in excluded:
            continue
        try:
            row = adapter(raw)
            validate_records([row])
        except (ValueError, KeyError) as exc:
            rejected.append({"id": raw["id"], "reason": str(exc)})
            continue
        if question_key(row["question"]) in excluded:
            continue
        excluded.add(row["id"])
        excluded.add(question_key(row["question"]))
        selected.append(row)
        if len(selected) == count:
            return selected, rejected
    raise RuntimeError(f"Only {len(selected)} valid examples available")


def main():
    from datasets import load_dataset
    from huggingface_hub import HfApi

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev-count", type=int, default=100)
    parser.add_argument("--eval-count", type=int, default=500)
    args = parser.parse_args()
    output = Path("data/processed/research")
    if output.exists():
        raise FileExistsError("Frozen output exists; do not overwrite splits")
    output.mkdir(parents=True)
    revision = HfApi().dataset_info("hotpotqa/hotpot_qa").sha
    hotpot = load_dataset("hotpotqa/hotpot_qa", "distractor", revision=revision)
    excluded = set()
    for path in (
        Path("data/processed/dev_set.json"),
        Path("data/processed/eval_set.json"),
    ):
        if path.exists():
            for row in json.loads(path.read_text()):
                excluded.update([row["id"], question_key(row["question"])])
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / "musique_v1.0.zip"
    if not archive.exists():
        import gdown

        result = gdown.download(
            id="1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h", output=str(archive), quiet=False
        )
        if result is None:
            raise RuntimeError("Official MuSiQue download failed")
    with zipfile.ZipFile(archive) as zipped:
        musique = {}
        for name in ("train", "dev"):
            members = [
                p
                for p in zipped.namelist()
                if p.endswith(f"musique_ans_v1.0_{name}.jsonl")
                and not p.startswith("__MACOSX")
            ]
            if len(members) != 1:
                raise ValueError("Ambiguous MuSiQue archive")
            musique[name] = [
                json.loads(line)
                for line in zipped.read(members[0]).decode().splitlines()
                if line.strip()
            ]
    manifest = {
        "seed": 20261110,
        "hotpot_revision": revision,
        "musique_zip_sha256": file_hash(archive),
        "sources": [
            "https://huggingface.co/datasets/hotpotqa/hotpot_qa",
            "https://github.com/StonyBrookNLP/musique/blob/main/download_data.sh",
        ],
        "licenses": {"hotpotqa": "CC BY-SA 4.0", "musique": "CC BY 4.0"},
        "datasets": {},
    }
    for name, train, val, adapter in [
        ("hotpotqa", hotpot["train"], hotpot["validation"], hotpot_record),
        ("musique", musique["train"], musique["dev"], musique_record),
    ]:
        dev, dev_rejected = choose(train, adapter, args.dev_count, set(excluded))
        ban = set(excluded) | {
            x for row in dev for x in (row["id"], question_key(row["question"]))
        }
        # Extra candidates permit deterministic removal of near duplicates.
        candidates, val_rejected = choose(val, adapter, args.eval_count + 100, ban)
        audit = duplicate_audit(dev, candidates)
        near_ids = {row["id"] for row in audit["matches"]}
        evaluation = [row for row in candidates if row["id"] not in near_ids][
            : args.eval_count
        ]
        assert len(evaluation) == args.eval_count
        entry = {
            "development_source": "official train",
            "evaluation_source": "official validation/dev (not hidden test)",
            "structural_rejections": dev_rejected + val_rejected,
            "duplicate_audit": audit,
            "splits": {},
        }
        for split, rows in [("development", dev), ("evaluation", evaluation)]:
            path = output / f"{name}_{split}.json"
            write_json(path, rows)
            entry["splits"][split] = {
                "path": str(path),
                "sha256": file_hash(path),
                "ids": [r["id"] for r in rows],
                "question_hashes": [
                    __import__("hashlib").sha256(r["question"].encode()).hexdigest()
                    for r in rows
                ],
                "counts": validate_records(rows),
            }
        manifest["datasets"][name] = entry
    write_json(Path("configs/splits/research_v1.json"), manifest)
    print("Frozen split manifest written; no model evaluation performed.")


if __name__ == "__main__":
    main()
