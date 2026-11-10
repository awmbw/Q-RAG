"""Model-ready GPU embedding throughput on a fixed development chunk workload."""

from pathlib import Path
from time import perf_counter

import numpy as np

from qrag.config import ExperimentConfig
from qrag.data import load_examples
from qrag.experiments.artifacts import environment, value_hash, write_json
from qrag.retrieval import chunk_document


def main():
    import torch
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer

    if not torch.cuda.is_available():
        raise RuntimeError("This declared GPU profile requires visible CUDA")
    torch.manual_seed(42)
    torch.set_num_threads(4)
    config = ExperimentConfig()
    snapshot = snapshot_download(
        config.embedding_model,
        revision=config.embedding_revision,
        local_files_only=True,
    )
    model = SentenceTransformer(snapshot, device="cuda", local_files_only=True)
    texts = []
    for query, _ in load_examples(
        Path("data/processed/research/hotpotqa_development.json")
    ):
        for document in query.documents:
            texts.extend(
                chunk.embedding_text
                for chunk in chunk_document(document, model.tokenizer)
            )
        if len(texts) >= 128:
            break
    texts = texts[:128]
    assert len(texts) == 128
    lengths = [
        len(model.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in texts
    ]
    assert max(lengths) <= min(240, model.max_seq_length)
    model.encode(
        texts[:8], batch_size=8, normalize_embeddings=True, show_progress_bar=False
    )
    torch.cuda.synchronize()
    rng = np.random.default_rng(42)
    rows = []
    reference = None
    for repeat in range(3):
        for batch in rng.permutation([1, 8, 32, 64]).tolist():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            started = perf_counter()
            vectors = model.encode(
                texts,
                batch_size=batch,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            torch.cuda.synchronize()
            seconds = perf_counter() - started
            if reference is None:
                reference = vectors
            difference = float(np.max(np.abs(vectors - reference)))
            assert difference < 1e-4
            rows.append(
                {
                    "repeat": repeat,
                    "batch_size": batch,
                    "seconds": seconds,
                    "chunks_per_second": len(texts) / seconds,
                    "unpadded_input_tokens_per_second": sum(lengths) / seconds,
                    "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "max_absolute_vector_difference_from_first_execution": difference,
                }
            )
    write_json(
        Path("docs/research_report/evidence/embedding_batch_profile.json"),
        {
            "scope": "one fixed 128-chunk development workload, model-ready GPU execution, three randomized batch-order repeats; not generator batching or a production load benchmark",
            "model": config.embedding_model,
            "revision": config.embedding_revision,
            "gpu": torch.cuda.get_device_name(0),
            "environment": environment(),
            "input_texts_sha256": value_hash(texts),
            "chunks": len(texts),
            "unpadded_input_tokens": sum(lengths),
            "maximum_input_tokens": max(lengths),
            "seed": 42,
            "records": rows,
            "median_by_batch": {
                str(batch): {
                    "seconds": float(
                        np.median(
                            [r["seconds"] for r in rows if r["batch_size"] == batch]
                        )
                    ),
                    "chunks_per_second": float(
                        np.median(
                            [
                                r["chunks_per_second"]
                                for r in rows
                                if r["batch_size"] == batch
                            ]
                        )
                    ),
                    "peak_gpu_bytes": max(
                        r["gpu_peak_allocated_bytes"]
                        for r in rows
                        if r["batch_size"] == batch
                    ),
                }
                for batch in [1, 8, 32, 64]
            },
        },
    )
    print("Completed 12 real GPU batch measurements on 128 fixed development chunks")


if __name__ == "__main__":
    main()
