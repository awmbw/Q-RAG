"""Describe observable failure signatures; do not infer unverified causal labels."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from qrag.data import load_examples
from qrag.evaluation import latest_records
from qrag.experiments.artifacts import atomic_text, write_json


def energy(row, indices):
    return sum(row["linear_coefficients"][i] for i in indices) + sum(
        row["pair_coefficients"][i][j]
        for offset, i in enumerate(indices)
        for j in indices[offset + 1 :]
    )


def main():
    report = {}
    lines = [
        "# Error signatures and examples",
        "",
        "These are automatically identified observations, not independently annotated causal explanations. Complete annotated support does not prove sufficient context, and an imperfect reference can affect F1. Cases are the first qualifying IDs in each frozen input order, rather than hand-picked winning examples.",
        "",
    ]
    for dataset in ["hotpotqa", "musique"]:
        examples = dict(
            (q.id, (q, labels))
            for q, labels in load_examples(
                Path(f"data/processed/research/{dataset}_evaluation.json")
            )
        )
        for generator in ["qwen15", "qwen3"]:
            stem = f"final_{dataset}_{generator}_count"
            manifest = json.loads(
                (Path("results") / stem / "manifest.json").read_text()
            )
            assert manifest["status"] in {"completed", "completed_with_errors"}
            rows = latest_records(Path("results") / stem / "predictions.jsonl")
            by_question = defaultdict(dict)
            for row in rows:
                by_question[row["question_id"]][row["method"]] = row
            counts = Counter()
            cases = defaultdict(list)
            for question_id, methods in by_question.items():
                full, top = methods["milp_full"], methods["top_k"]
                if full["status"] != "success" or top["status"] != "success":
                    counts["comparison_has_execution_failure"] += 1
                    continue
                assert full["candidate_ids"] == top["candidate_ids"]
                top_energy = energy(full, top["selection"]["indices"])
                flags = []
                if full["selection"]["optimal"] and full["metrics"]["answer_f1"] < 1:
                    flags.append("certified_optimum_with_imperfect_answer")
                if (
                    full["metrics"]["all_supporting_documents"] == 1
                    and full["metrics"]["answer_f1"] < 1
                ):
                    flags.append("complete_annotated_support_with_imperfect_answer")
                if (
                    full["full_energy"] < top_energy - 1e-6
                    and full["metrics"]["answer_f1"] < top["metrics"]["answer_f1"]
                ):
                    flags.append("lower_common_energy_but_worse_answer_than_relevance")
                if (
                    full["metrics"]["document_recall"] < 1
                    and full["metrics"]["answer_f1"] == 1
                ):
                    flags.append("correct_answer_without_all_annotated_support")
                for flag in flags:
                    counts[flag] += 1
                    if len(cases[flag]) < 2:
                        query, labels = examples[question_id]
                        cases[flag].append(
                            {
                                "question_id": question_id,
                                "question": query.question,
                                "reference": labels.answer,
                                "aliases": list(labels.aliases),
                                "optimized_answer": full["answer"],
                                "relevance_answer": top["answer"],
                                "optimized_f1": full["metrics"]["answer_f1"],
                                "relevance_f1": top["metrics"]["answer_f1"],
                                "optimized_full_energy": full["full_energy"],
                                "relevance_under_same_full_energy": top_energy,
                                "optimized_selected_ids": full["selected_ids"],
                                "relevance_selected_ids": top["selected_ids"],
                                "optimized_support_recall": full["metrics"][
                                    "document_recall"
                                ],
                            }
                        )
            report[stem] = {
                "questions": len(by_question),
                "signature_counts": dict(counts),
                "examples": dict(cases),
            }
            lines += [
                f"## {dataset} / {generator}",
                "",
                "| Observation | Questions |",
                "| --- | ---: |",
            ]
            lines += [
                f"| {flag.replace('_', ' ')} | {count} |"
                for flag, count in counts.items()
            ]
            for flag, values in cases.items():
                lines += ["", f"### {flag.replace('_', ' ')}", ""]
                for case in values:
                    lines.append(
                        f"- `{case['question_id']}`: {case['question']} Reference: {case['reference']!r}. MILP: {case['optimized_answer']!r} (F1 {case['optimized_f1']:.4f}); relevance: {case['relevance_answer']!r} (F1 {case['relevance_f1']:.4f}). Same-objective energies: MILP {case['optimized_full_energy']:.5f}, relevance {case['relevance_under_same_full_energy']:.5f}."
                    )
            lines += [""]
    write_json(Path("paper/results/error_signatures.json"), report)
    atomic_text(Path("paper/results/error_analysis.md"), "\n".join(lines) + "\n")
    print(
        "Generated descriptive signatures and deterministic examples for four main conditions"
    )


if __name__ == "__main__":
    main()
