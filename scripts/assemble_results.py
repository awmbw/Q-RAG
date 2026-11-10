"""Assemble traceable tables, figures and manuscript text from completed frozen runs."""

import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from export_run import export
from figure_export import save_figure
from resource_summary import add_circuit_summaries

from qrag.evaluation import latest_records, paired_interval, question_scores
from qrag.experiments.artifacts import atomic_text, write_json
from qrag.experiments.report import report


def fmt(value, digits=4):
    return "-" if value is None else f"{value:.{digits}f}"


def grouped_values(rows, callback):
    output = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["status"] != "success":
            continue
        value = callback(row)
        if value is not None:
            output[re.sub(r"_s\d+$", "", row["method"])][row["question_id"]].append(
                value
            )
    return {
        m: {q: float(np.mean(v)) for q, v in questions.items()}
        for m, questions in output.items()
    }


def replace_block(text, name, content):
    pattern = rf"<!-- BEGIN {name} -->.*?<!-- END {name} -->"
    result, count = re.subn(
        pattern,
        f"<!-- BEGIN {name} -->\n{content}\n<!-- END {name} -->",
        text,
        flags=re.S,
    )
    if count != 1:
        raise ValueError("Missing/duplicate manuscript block " + name)
    return result


def main():
    matrix = json.loads(Path("configs/final_matrix.json").read_text())
    secondary = json.loads(Path("configs/formulation_controls.json").read_text())
    stems = [Path(e["config"]).stem for e in matrix["configs"] + secondary["configs"]]
    stems += ["final_hotpotqa_gatecap", "final_musique_gatecap"]
    preparation = json.loads(Path("configs/preparation_control.json").read_text())
    stems += [Path(e["config"]).stem for e in preparation["configs"]]
    output = Path("paper/results")
    output.mkdir(parents=True, exist_ok=True)
    evidence = Path("docs/research_report/evidence")
    figures = Path("paper/figures")
    figures.mkdir(parents=True, exist_ok=True)
    analyses = {}
    configurations = {}
    quantum_points = {}
    primary_count = 0
    for stem in stems:
        run = Path("results") / stem
        metadata = json.loads((run / "manifest.json").read_text())
        if metadata["status"] not in {"completed", "completed_with_errors"}:
            raise ValueError("Incomplete run " + stem)
        rows = latest_records(run / "predictions.jsonl")
        result = report(
            run,
            output / (stem + "_analysis"),
            reference="gate_absolute" if stem.endswith("_gatecap") else "milp_full",
        )
        add_circuit_summaries(result, rows)
        scores = question_scores(rows)
        if "milp_base" in scores and "milp_full" in scores:
            result["graph_minus_base_f1"] = paired_interval(
                scores["milp_full"], scores["milp_base"]
            )
        if "xy_base_p1" in scores and "xy_full_p1" in scores:
            result["qaoa_graph_minus_base_f1"] = paired_interval(
                scores["xy_full_p1"], scores["xy_base_p1"]
            )
        if "prepared_base_p1" in scores:
            result["prepared_graph_minus_base_f1"] = paired_interval(
                scores["prepared_full_p1"], scores["prepared_base_p1"]
            )
            result["prepared_evidence_minus_absolute_f1"] = paired_interval(
                scores["prepared_evidence_f0.5"], scores["prepared_absolute_f0.5"]
            )
        if "gate_evidence" in scores and "gate_absolute" in scores:
            result["gate_evidence_minus_absolute_f1"] = paired_interval(
                scores["gate_evidence"], scores["gate_absolute"]
            )
        result["output_limit_hits"] = sum(
            r.get("hit_output_limit", False) for r in rows if r["status"] == "success"
        )
        result["successful_distinct_generation_records"] = sum(
            not r.get("generation_reused", False)
            for r in rows
            if r["status"] == "success"
        )
        result["failure_types"] = {
            name: sum(
                r["status"] != "success" and r.get("error_type") == name for r in rows
            )
            for name in sorted(
                {r.get("error_type") for r in rows if r["status"] != "success"}
            )
        }
        methods = {m["name"]: m for m in metadata["identity"]["spec"]["methods"]}
        reference = {
            r["question_id"]: r
            for r in rows
            if r["method"] == "milp_full"
            and r["status"] == "success"
            and r["selection"]["optimal"]
        }
        gap_values = defaultdict(list)
        for row in rows:
            if (
                row["status"] == "success"
                and row["question_id"] in reference
                and methods[row["method"]].get(
                    "gamma", 0.2 if stem.endswith("_gatecap") else 0
                )
                == 0.2
            ):
                difference = (
                    row["full_energy"] - reference[row["question_id"]]["full_energy"]
                )
                assert difference >= -1e-5, (stem, row["method"], difference)
                gap_values[re.sub(r"_s\d+$", "", row["method"])].append(difference)
        result["certified_full_energy_gap_successful_only"] = {
            m: float(np.mean(values)) for m, values in gap_values.items()
        }
        candidates = grouped_values(
            rows, lambda r: r.get("candidate_metrics", {}).get("document_recall")
        )
        result["candidate_recall_successful_only"] = {
            m: float(np.mean(list(values.values()))) for m, values in candidates.items()
        }
        result["selection_diagnostics_successful_only"] = {}
        for metric, callback in {
            "selected_count": lambda r: r.get("selected_count"),
            "certified_optimal_fraction": lambda r: (
                float(r["selection"]["optimal"]) if r.get("selection") else None
            ),
        }.items():
            result["selection_diagnostics_successful_only"][metric] = {
                m: float(np.mean(list(values.values())))
                for m, values in grouped_values(rows, callback).items()
            }
        analyses[stem] = result
        configurations[stem] = metadata["identity"]["spec"]
        write_json(output / (stem + "_analysis.json"), result)
        export(run, evidence / (stem + ".json"), compress=True)
        if stem in [Path(e["config"]).stem for e in matrix["configs"]]:
            primary_count += len(rows)
        if stem in ["final_hotpotqa_quantum", "final_musique_quantum"]:
            quantum_points[stem] = {"scores": scores, "resources": result["table"]}
        print("Assembled", stem, len(rows), "records", flush=True)
    assert primary_count == 50290
    write_json(
        output / "overview.json",
        {
            "primary_method_question_evaluations": primary_count,
            "runs": analyses,
            "note": "Definitive cycle 2 plus separately declared secondary controls; cycle 1 excluded.",
        },
    )
    # Static publication figure; points are complete compiled circuits, not semantic edge counts.
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8), sharey=True)
    points = [
        ("xy_full_p1", "Basis-start full XY", "#375d85", "o"),
        ("xy_absolute_f0.5", "Magnitude half", "#cb8a31", "s"),
        ("xy_evidence_f0.5", "Evidence half", "#178272", "D"),
        ("penalty_full", "Penalty full", "#a45b74", "^"),
    ]
    for axis, (stem, data) in zip(axes, quantum_points.items(), strict=True):
        for method, label, color, marker in points:
            values = data["scores"][method]
            zeros = dict.fromkeys(values, 0.0)
            interval = paired_interval(values, zeros)
            mean = interval["mean_difference"]
            low, high = interval["ci95"]
            gates = data["resources"][method][
                "line_two_qubit_gates_all_completed_circuits"
            ]
            axis.errorbar(
                gates,
                mean,
                yerr=[[mean - low], [high - mean]],
                fmt=marker,
                color=color,
                capsize=3,
                label=label,
                markersize=6,
            )
        axis.set_title("HotpotQA" if "hotpotqa" in stem else "MuSiQue")
        axis.set_xlabel("Complete compiled line two-qubit gates (mean)")
        axis.grid(alpha=0.18)
        axis.set_ylim(0, 1)
    axes[0].set_ylabel("Answer F1 (0-1), question-level 95% interval")
    axes[1].legend(loc="upper right", frameon=False, fontsize=8)
    fig.suptitle(
        "Quantum context selection: observed quality and complete circuit cost",
        fontsize=11,
    )
    fig.tight_layout()
    for suffix in ["png", "svg"]:
        save_figure(fig, figures / ("quality_resources." + suffix))
    plt.close(fig)
    # Traceable main text, using a bounded set of headline rows and full linked appendices.
    classical = [
        "| Dataset / generator | Method | N | Answer F1 | EM |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        for tag in ["qwen15", "qwen3"]:
            table = analyses[f"final_{dataset}_{tag}_count"]["table"]
            for method in [
                "top_k",
                "bm25",
                "reranker",
                "coverage",
                "milp_base",
                "milp_full",
            ]:
                row = table[method]
                classical.append(
                    f"| {dataset} / {tag} | {method} | {row['questions']} | {fmt(row['answer_f1'])} | {fmt(row['answer_em'])} |"
                )
    quantum = [
        "| Dataset | Method | Answer F1 | Feasible shots | Line 2Q gates |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        table = analyses[f"final_{dataset}_quantum"]["table"]
        for method in [
            "milp_full",
            "random_full",
            "xy_full_p1",
            "xy_full_p2",
            "xy_absolute_f0.5",
            "xy_evidence_f0.5",
            "penalty_full",
            "penalty_absolute",
            "penalty_evidence",
        ]:
            row = table[method]
            quantum.append(
                f"| {dataset} | {method} | {fmt(row['answer_f1'])} | {fmt(row.get('feasible_fraction_all_completed_circuits'))} | {fmt(row.get('line_two_qubit_gates_all_completed_circuits'), 1)} |"
            )
    paired = [
        "| Dataset | Evidence minus magnitude F1 | 95% paired interval |",
        "| --- | ---: | --- |",
    ]
    directions = []
    for dataset in ["hotpotqa", "musique"]:
        comparison = analyses[f"final_{dataset}_quantum"][
            "principal_evidence_minus_absolute_f1"
        ]
        paired.append(
            f"| {dataset} | {fmt(comparison['mean_difference'])} | [{fmt(comparison['ci95'][0])}, {fmt(comparison['ci95'][1])}] |"
        )
        directions.append(comparison)
    gate = [
        "| Dataset | Rule | N | F1 | Mean line 2Q | Failed records |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        for method, row in analyses[f"final_{dataset}_gatecap"]["table"].items():
            gate.append(
                f"| {dataset} | {method} | {row['questions']} | {fmt(row['answer_f1'])} | {fmt(row['line_two_qubit_gates_successful_only'], 1)} | {row['failures']} |"
            )
    failures = sum(
        v["failures"]
        for stem, analysis in analyses.items()
        if not stem.endswith("_gatecap")
        for v in analysis["table"].values()
    )
    preparation_lines = [
        "### Exploratory feasible-superposition control",
        "",
        "The frozen XY implementation starts from a basis state. Its first diagonal cost layer contributes only a global phase; at p=1 its cost angle cannot affect probabilities. We retained those results and separately added one fixed pi/4 XY ring sweep before the first cost layer. This creates a feasible, generally nonuniform superposition and makes subsequent cost phases observable after mixing. The added sweep is included in complete compilation. This control was introduced after the analytic diagnosis and is exploratory, not a replacement for the principal frozen comparison.",
        "",
        "| Dataset | Prepared method | F1 | Mean complete line 2Q |",
        "| --- | --- | ---: | ---: |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        for method in [
            "prepared_base_p1",
            "prepared_full_p1",
            "prepared_full_p2",
            "prepared_absolute_f0.5",
            "prepared_evidence_f0.5",
        ]:
            row = analyses[f"final_{dataset}_prepared"]["table"][method]
            preparation_lines.append(
                f"| {dataset} | {method} | {fmt(row['answer_f1'])} | {fmt(row['line_two_qubit_gates_all_completed_circuits'], 1)} |"
            )
    additional_lines = [
        "### Formulation effects and token-budget sensitivity",
        "",
        "| Dataset / generator | Budget | N | Graph minus base F1 | 95% paired interval |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        for tag in ["qwen15", "qwen3"]:
            for budget in ["count", "tokens"]:
                comparison = analyses[f"final_{dataset}_{tag}_{budget}"][
                    "graph_minus_base_f1"
                ]
                additional_lines.append(
                    f"| {dataset} / {tag} | {budget} | {comparison['questions']} | {fmt(comparison['mean_difference'])} | [{fmt(comparison['ci95'][0])}, {fmt(comparison['ci95'][1])}] |"
                )
    additional_lines += [
        "",
        "The graph feature's effect varies across settings; these exploratory intervals all include zero. Count conditions use 500 questions, whereas the 1,200-token-cap conditions use the first 100 frozen IDs. Their raw means cannot establish a count-versus-token causal effect across different question populations. The cap is checked against actual formatted context; observed consumption varies below it.",
        "",
        "### Bounded corpus retrieval",
        "",
        "| Dataset | Candidates | N | Candidate support recall | Coverage F1 | Full MILP F1 | MILP certified fraction |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset in ["hotpotqa", "musique"]:
        for size in [25, 50, 100]:
            analysis = analyses[f"final_{dataset}_corpus{size}"]
            table = analysis["table"]
            additional_lines.append(
                f"| {dataset} | {size} | {table['milp_full']['questions']} | {fmt(analysis['candidate_recall_successful_only']['milp_full'])} | {fmt(table['coverage']['answer_f1'])} | {fmt(table['milp_full']['answer_f1'])} | {fmt(analysis['selection_diagnostics_successful_only']['certified_optimal_fraction']['milp_full'])} |"
            )
    additional_lines += [
        "",
        "The 25-candidate condition uses 100 questions; 50/100-candidate conditions use the same first 30 IDs. Candidate recall is measured before selection, using annotations only during evaluation. Increasing a pool can recover annotated support while also increasing optimization difficulty and adding distractors. The one-second MILP setting can return feasible incumbents without an optimality certificate. Larger-pool results do not demonstrate quantum scaling.",
        "",
    ]
    signatures = json.loads((output / "error_signatures.json").read_text())
    additional_lines += [
        "### Objective quality is not answer quality",
        "",
        "Across the four 500-question fixed-count conditions, full MILP has lower common-objective energy but worse F1 than relevance selection on respectively "
        + ", ".join(
            str(
                signatures[f"final_{d}_{g}_count"]["signature_counts"].get(
                    "lower_common_energy_but_worse_answer_than_relevance", 0
                )
            )
            for d in ["hotpotqa", "musique"]
            for g in ["qwen15", "qwen3"]
        )
        + " questions (HotpotQA 1.5B/3B, MuSiQue 1.5B/3B). The relevance subset is rescored using the full MILP coefficients for this comparison. These observations directly distinguish proxy optimization from downstream correctness; they do not independently identify a causal graph or generator error. Deterministic examples and additional signatures are released.",
        "",
    ]
    results = "\n".join(
        [
            "### Classical supplied-pool answers",
            "",
            *classical,
            "",
            "F1/EM use a 0-1 scale. Each main condition has 500 questions. The complete method tables, token lengths, failures and paired intervals are released with the artifacts; selected headline rows above do not replace them.",
            "",
            "### Quantum quality, feasibility and complete cost",
            "",
            *quantum,
            "",
            "The quantum conditions use the same 50 reduced-pool questions per dataset. Three seeds are averaged within question for F1. Feasibility and gate means include all completed circuits, including zero-feasible-sample failures. Classical rows have no quantum gate count rather than an invented zero. Gates describe a complete compiled circuit on the synthetic line.",
            "",
            "### Principal half-edge comparison",
            "",
            *paired,
            "",
            "These intervals compare evidence guidance with magnitude retention on identical questions and budgets. An interval spanning zero does not establish equality or noninferiority.",
            "",
            "![Figure 2. Mean answer F1 and complete compiled circuit cost. Error bars resample questions after averaging solver seeds. Synthetic line compilation is not a physical-device timing measurement.](figures/quality_resources.png)",
            "",
            "### Secondary complete-gate-cap control",
            "",
            *gate,
            "",
            "The cap is 180 complete compiled line two-qubit gates. Retention is chosen using declared inference-only prefix trials and verified after angle optimization. Infeasible penalty encodings and final-cap violations remain failures. Actual resource consumption can differ below a shared cap.",
            "",
            "### Additional settings and failures",
            "",
            f"The definitive primary matrix contains {primary_count:,} method/question evaluations. Outside the deliberately restrictive gate-cap diagnostic, the grouped tables contain {failures} failed method records. Token studies, bounded corpora, larger-quantum sensitivities and the base/graph QAOA control are separately tabulated in the released result directory. Their smaller samples are not pooled into the principal comparison.",
            "",
            "All aggregate values derive from question-level artifacts. Successful-only resource summaries exclude failed executions and are labeled accordingly. Timings are descriptive laptop measurements; software packaging tasks ran concurrently with parts of evaluation, so they are not isolated production-throughput benchmarks.",
            "",
            *preparation_lines,
            "",
            *additional_lines,
        ]
    )
    positives = sum(c["ci95"][0] > 0 for c in directions)
    negatives = sum(c["ci95"][1] < 0 for c in directions)
    interpretation = (
        "Evidence guidance has a positive paired interval on both datasets under this setup."
        if positives == 2
        else "Evidence guidance does not show a consistently positive paired interval across both datasets under this setup."
    )
    abstract = (
        "We evaluate context selection for multi-hop retrieval augmented generation using the quantum approximate optimization algorithm (QAOA), classical references and complete circuit compilation. "
        f"The frozen primary matrix contains {primary_count:,} method/question evaluations over 1,000 distinct held-out questions, including two Qwen generators and 50-question quantum conditions per dataset with three seeds. "
        "We separate scoring quality, sparse-objective quality and solver behavior. Squared count penalties introduce all-pairs couplings; count-preserving mixing avoids this densification but adds its own cost. "
        f"The principal evidence-minus-magnitude answer F1 differences are {fmt(directions[0]['mean_difference'])} on HotpotQA and {fmt(directions[1]['mean_difference'])} on MuSiQue, with both paired 95% intervals crossing zero. "
        "We identify an inactive first cost phase in the basis-start depth-one circuit and retain its results alongside an exploratory feasible-superposition control; neither supports a consistent evidence-guidance benefit. "
        "Uniform feasible sampling is a strong reference when only 252 subsets exist. Lexical coverage has the highest observed F1 in all four main classical count conditions. "
        "We release question outcomes, frozen optimization instances, source snapshots and resource metadata. All quantum execution is simulated; practical quantum advantage is not established."
    )
    conclusion = (
        "Constraint encoding is part of the sparsification method, not an accounting detail. A sparse semantic objective can become dense again after a cardinality penalty, while a feasible-subspace mixer has an explicit resource cost. "
        + interpretation
        + " Strong classical and same-sample random controls remain essential when the feasible space is small. "
        "State preparation also determines whether a cost layer can affect probabilities, and the exploratory prepared results do not establish a consistent evidence-guidance gain. "
        "The released pipeline supports transparent future hardware and stronger-evidence studies, but the present results do not establish practical quantum advantage or guaranteed evidence preservation."
    )
    paper = Path("paper/manuscript.md")
    text = paper.read_text()
    text = replace_block(text, "ABSTRACT", abstract)
    text = replace_block(text, "RESULTS", results)
    text = replace_block(text, "CONCLUSION", conclusion)
    text = text.replace(
        "Author details and submission formatting require final approval. ", ""
    )
    atomic_text(paper, text)
    atomic_text(
        output / "main_results.md",
        results.replace("](figures/", "](../figures/") + "\n",
    )
    write_json(
        output / "claim_summary.json",
        {
            "principal_positive_intervals": positives,
            "principal_negative_intervals": negatives,
            "interpretation": interpretation,
            "primary_evaluations": primary_count,
            "quantum_hardware": False,
            "quantum_advantage_established": False,
        },
    )


if __name__ == "__main__":
    main()
