"""Question-level paired uncertainty, keeping solver repeats inside each question."""

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np


def latest_records(path):
    records = {}
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        records[(row["question_id"], row["method"])] = row
    return list(records.values())


def question_scores(records, metric="answer_f1", group_seeds=True):
    groups = defaultdict(lambda: defaultdict(list))
    for row in records:
        method = re.sub(r"_s\d+$", "", row["method"]) if group_seeds else row["method"]
        value = (
            row.get("metrics", {}).get(metric, 0.0)
            if row["status"] == "success"
            else 0.0
        )
        groups[method][row["question_id"]].append(value)
    return {
        method: {q: float(np.mean(values)) for q, values in questions.items()}
        for method, questions in groups.items()
    }


def paired_interval(first, second, resamples=10000, seed=20261110):
    if set(first) != set(second) or not first:
        raise ValueError("Paired comparison requires the same nonempty question set")
    ids = sorted(first)
    differences = np.array([first[q] - second[q] for q in ids])
    rng = np.random.default_rng(seed)
    means = []
    # Bounded memory even for large studies.
    for start in range(0, resamples, 500):
        count = min(500, resamples - start)
        means.extend(
            np.mean(
                differences[rng.integers(0, len(ids), size=(count, len(ids)))], axis=1
            ).tolist()
        )
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "questions": len(ids),
        "mean_difference": float(differences.mean()),
        "ci95": [float(low), float(high)],
        "resamples": resamples,
        "seed": seed,
        "method": "paired question bootstrap; solver repeats averaged within question",
    }


def analyze(records, reference=None):
    grouped = question_scores(records)
    grouped_em = question_scores(records, metric="answer_em")
    reference = reference or (
        "milp_full"
        if "milp_full" in grouped
        else "top_k"
        if "top_k" in grouped
        else next(iter(grouped))
    )
    table = {}
    for method, scores in sorted(grouped.items()):
        rows = [r for r in records if re.sub(r"_s\d+$", "", r["method"]) == method]
        good = [r for r in rows if r["status"] == "success"]
        summary = {
            "questions": len(scores),
            "attempted_method_records": len(rows),
            "failures": len(rows) - len(good),
            "answer_f1": float(np.mean(list(scores.values()))),
            "answer_em": float(np.mean(list(grouped_em[method].values()))),
        }
        for key in [
            "context_tokens",
            "input_tokens",
            "selection_seconds",
            "actual_generation_seconds",
            "full_energy",
        ]:
            values = [r[key] for r in good if key in r]
            summary[key + "_successful_only"] = (
                float(np.mean(values)) if values else None
            )
        for key in ["document_recall", "all_supporting_documents"]:
            values = [
                r["metrics"][key] for r in good if r["metrics"].get(key) is not None
            ]
            summary[key + "_successful_only"] = (
                float(np.mean(values)) if values else None
            )
        resources = [r["resources"] for r in good if r.get("resources")]
        for key in ["feasible_fraction"]:
            values = [r[key] for r in resources if key in r]
            summary[key + "_successful_only"] = (
                float(np.mean(values)) if values else None
            )
        for target in ["all_to_all", "line"]:
            values = [r[target]["two_qubit_gates"] for r in resources if target in r]
            summary[target + "_two_qubit_gates_successful_only"] = (
                float(np.mean(values)) if values else None
            )
        table[method] = summary
    comparisons = {
        method: paired_interval(scores, grouped[reference])
        for method, scores in grouped.items()
        if method != reference and set(scores) == set(grouped[reference])
    }
    principal = None
    if "xy_evidence_f0.5" in grouped and "xy_absolute_f0.5" in grouped:
        principal = paired_interval(
            grouped["xy_evidence_f0.5"], grouped["xy_absolute_f0.5"]
        )
    return {
        "reference": reference,
        "table": table,
        "paired_differences_to_reference": comparisons,
        "principal_evidence_minus_absolute_f1": principal,
        "interpretation": "Exploratory intervals unless a comparison is explicitly primary in the frozen protocol. No noninferiority or hardware-speedup claim.",
    }
