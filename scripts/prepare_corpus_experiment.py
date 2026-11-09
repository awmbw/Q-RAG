"""Freeze bounded-corpus candidates independently of answer/support annotations."""

import json
from dataclasses import asdict
from pathlib import Path

from qrag.config import ExperimentConfig
from qrag.corpus import CorpusRetriever, corpus_id
from qrag.data import load_examples
from qrag.experiments.artifacts import file_hash, write_json
from qrag.retrieval import ChunkEncoder


def main():
    from sentence_transformers import SentenceTransformer

    config = ExperimentConfig()
    model = SentenceTransformer(
        config.embedding_model,
        revision=config.embedding_revision,
        device="cuda",
        local_files_only=True,
    )
    encoder = ChunkEncoder(
        model,
        Path(".cache/study_embeddings.sqlite"),
        config.embedding_model,
        config.embedding_revision,
    )
    manifest = {
        "scope": "bounded benchmark-input union; sources chosen without labels; no full-Wikipedia claim",
        "datasets": {},
    }
    for dataset in ["hotpotqa", "musique"]:
        directory = Path(".cache") / ("corpus_" + dataset)
        input_paths = [
            Path(f"data/processed/research/{dataset}_{split}.json")
            for split in ["development", "evaluation"]
        ]
        examples = [item for path in input_paths for item in load_examples(path)]
        retriever = CorpusRetriever.build(
            directory, [d for q, _ in examples for d in q.documents], encoder
        )
        original = json.loads(input_paths[1].read_text())[:100]
        output = {size: [] for size in [25, 50, 100]}
        reports = []
        for number, row in enumerate(original):
            selected, profile = retriever.retrieve(
                row["question"], 100, unique_titles=dataset == "hotpotqa"
            )
            # Only evaluation mapping below reads support labels. Selection above
            # accepts just the question and corpus, not this record's labels.
            support_ids = [
                corpus_id(d["title"], d["text"])
                for i, d in enumerate(row["documents"])
                if f"{row['id']}:d{i}" in row.get("supporting_ids", [])
            ]
            for size in output:
                modified = {
                    **row,
                    "candidate_source": "retrieved",
                    "documents": [asdict(d) for d in selected[:size]],
                    "supporting_ids": support_ids,
                    "retrieval": profile,
                }
                output[size].append(modified)
            reports.append(profile)
        entry = {
            "corpus": retriever.manifest,
            "inputs": {str(p): file_hash(p) for p in input_paths},
            "candidate_files": {},
            "retrieval_profiles": reports,
        }
        for size, rows in output.items():
            path = Path(f"data/processed/research/{dataset}_corpus_{size}.json")
            if path.exists():
                raise FileExistsError("Refusing to overwrite frozen corpus candidates")
            write_json(path, rows)
            entry["candidate_files"][str(size)] = {
                "path": str(path),
                "sha256": file_hash(path),
                "questions": len(rows),
            }
        manifest["datasets"][dataset] = entry
        print(dataset, retriever.manifest["documents"], "documents", flush=True)
    write_json(Path("configs/splits/corpus_v1.json"), manifest)
    encoder.cache.close()


if __name__ == "__main__":
    main()
