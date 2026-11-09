"""Create an unjudged source-grounded graph review sheet without reference labels."""

from pathlib import Path

import numpy as np

from qrag.data import load_examples
from qrag.evaluation import latest_records
from qrag.evidence import cached_evidence
from qrag.experiments.artifacts import file_hash, write_json


def main():
    samples = []
    sources = {}
    for dataset in ["hotpotqa", "musique"]:
        source = Path(f"results/calibrate_{dataset}/predictions.jsonl")
        rows = {
            r["question_id"]: r
            for r in latest_records(source)
            if r["method"] == "milp_g0.2" and r["status"] == "success"
        }
        sources[dataset] = file_hash(source)
        examples = load_examples(
            Path(f"data/processed/research/{dataset}_development.json")
        )[:10]
        for query, _ in examples:
            row = rows[query.id]
            relevance = -np.asarray(row["linear_coefficients"])
            assert row["candidate_ids"] == [d.id for d in query.documents]
            _, _, graph = cached_evidence(
                query, relevance, Path(".cache/annotation_graphs.sqlite")
            )
            lookup = {d.id: d for d in query.documents}
            edges = []
            for edge in graph["edges"][:2]:
                mentions = {}
                for document_id in [edge["source"], edge["target"]]:
                    doc = lookup[document_id]
                    mentions[document_id] = [
                        {
                            **m,
                            "source_excerpt": doc.text[
                                max(0, m["start"] - 35) : m["end"] + 35
                            ],
                        }
                        for m in graph["mentions"][document_id]
                        if m["entity"] in edge["entities"]
                    ]
                edges.append(
                    {
                        **edge,
                        "mentions": mentions,
                        "canonical_mentions_same_entity": None,
                        "jointly_required_for_question": None,
                        "reviewer": None,
                        "reviewed_at": None,
                        "notes": None,
                    }
                )
            samples.append(
                {
                    "dataset": dataset,
                    "question_id": query.id,
                    "question": query.question,
                    "extractor_revision": graph["extractor_revision"],
                    "total_edges": len(graph["edges"]),
                    "sampled_edges": edges,
                }
            )
    write_json(
        Path("docs/research_report/annotation_sample.json"),
        {
            "status": "unjudged worksheet; not measured semantic extraction accuracy",
            "policy": "first ten frozen development IDs per dataset, first two extracted edges per question; retain questions with no edges; convenience sample, not a representative accuracy estimate",
            "reference_annotations_used": False,
            "source_prediction_hashes": sources,
            "samples": samples,
        },
    )
    print(
        "Prepared",
        len(samples),
        "unjudged development questions and",
        sum(len(s["sampled_edges"]) for s in samples),
        "edge examples",
    )


if __name__ == "__main__":
    main()
