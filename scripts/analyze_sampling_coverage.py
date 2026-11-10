"""Report exact sampling distributions on the development-derived instances."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from figure_export import save_figure

from qrag.evaluation import paired_interval
from qrag.experiments.artifacts import atomic_text, write_json


def replace_block(text, name, content):
    start, end = f"<!-- BEGIN {name} -->", f"<!-- END {name} -->"
    if start in text:
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        return before + start + "\n" + content + "\n" + end + after
    location = "## 9. Limitations and threats to validity"
    return text.replace(
        location, start + "\n" + content + "\n" + end + "\n\n" + location
    )


def main():
    evidence = json.loads(
        Path("docs/research_report/evidence/sampling_coverage.json").read_text()
    )
    assert len(evidence["records"]) == 480
    grouped = defaultdict(lambda: defaultdict(list))
    for record in evidence["records"]:
        for budget in record["budgets"]:
            size = record["n"], record["mixer"], budget["samples"]
            grouped[size][record["question_id"]].append(budget)
    summary = []
    for (n, mixer, samples), questions in sorted(grouped.items()):
        metrics = {}
        for key in [
            "uniform_optimum_probability",
            "qaoa_optimum_probability",
            "qaoa_no_feasible_probability",
            "uniform_expected_gap",
            "qaoa_expected_gap_given_feasible",
        ]:
            per_question = {
                q: mean(v[key] for v in values) for q, values in questions.items()
            }
            metrics[key] = {
                "mean": mean(per_question.values()),
                "question_bootstrap": paired_interval(
                    per_question, dict.fromkeys(per_question, 0.0)
                ),
            }
        difference = {
            q: mean(
                v["qaoa_optimum_probability"] - v["uniform_optimum_probability"]
                for v in values
            )
            for q, values in questions.items()
        }
        metrics["qaoa_minus_uniform_optimum_probability"] = paired_interval(
            difference, dict.fromkeys(difference, 0.0)
        )
        summary.append(
            {
                "n": n,
                "mixer": mixer,
                "samples": samples,
                "questions": len(questions),
                **metrics,
            }
        )
    output = Path("paper/results")
    output.mkdir(parents=True, exist_ok=True)
    write_json(
        output / "sampling_coverage_summary.json",
        {
            "rows": summary,
            "scope": "20 development questions, nested candidate sizes, exact trained simulation distributions; no answer labels, held-out claim or hardware advantage",
            "cost_boundary": "QAOA additionally uses up to 64 exact-expectation objective evaluations. Uniform feasible draws require no angle training. Counts compare final draws, not equal total computation.",
        },
    )
    lookup = {(r["n"], r["mixer"], r["samples"]): r for r in summary}
    fig, grid = plt.subplots(2, 2, figsize=(7.5, 5.4), sharey=True)
    axes = grid.ravel()
    budgets = evidence["spec"]["sample_budgets"]
    for axis, n in zip(axes, evidence["spec"]["candidate_sizes"]):
        for mixer, color, label in [
            ("xy", "#178272", "Basis-start XY"),
            ("penalty", "#cb8a31", "Penalty QAOA"),
        ]:
            axis.plot(
                budgets,
                [
                    lookup[n, mixer, s]["qaoa_optimum_probability"]["mean"]
                    for s in budgets
                ],
                "o-",
                color=color,
                label=label,
                markersize=3,
            )
        axis.plot(
            budgets,
            [
                lookup[n, "xy", s]["uniform_optimum_probability"]["mean"]
                for s in budgets
            ],
            "--",
            color="#375d85",
            label="Uniform feasible",
        )
        axis.set_xscale("log", base=2)
        axis.set_xticks([1, 16, 256, 1024], ["1", "16", "256", "1,024"])
        axis.set_ylim(0, 1.03)
        axis.set_title(f"n={n}, k=5")
        axis.set_xlabel("Final draws")
        axis.grid(alpha=0.18)
    axes[0].set_ylabel("P(sample a full optimum)")
    axes[2].set_ylabel("P(sample a full optimum)")
    axes[-1].legend(fontsize=7, loc="upper left")
    fig.suptitle(
        "Repeated sampling on 20 development-derived instances (ideal distributions)",
        fontsize=10,
    )
    fig.tight_layout()
    figures = Path("paper/figures")
    figures.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        save_figure(fig, figures / ("sampling_coverage." + suffix))
    plt.close(fig)
    lines = [
        "### Development-derived sampling mechanism study",
        "",
        "To separate trained distribution quality from best-of-many selection, we train p=1 circuits on 20 development-derived coefficient instances at each of n=8,10,12,16, with k=5 and three seeds per encoding. These are 480 numerical circuit solves, not additional held-out answer evaluations. For single-draw optimum mass u, the probability of seeing an optimum in S draws is 1-(1-u)^S. We compute this directly from the trained ideal statevector distribution and enumerate feasible energies. This calculation does not estimate a physical device's output distribution.",
        "",
        "| Candidates | Encoding | Uniform P(optimum), 1,024 draws | QAOA P(optimum), 1,024 draws | Conditional QAOA energy gap |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for n in evidence["spec"]["candidate_sizes"]:
        for mixer in ["xy", "penalty"]:
            row = lookup[n, mixer, 1024]
            lines.append(
                f"| {n} | {mixer} | {row['uniform_optimum_probability']['mean']:.4f} | {row['qaoa_optimum_probability']['mean']:.4f} | {row['qaoa_expected_gap_given_feasible']['mean']:.4f} |"
            )
    lines += [
        "",
        "Means average seeds within question first. Conditional gaps describe the best feasible sample given that at least one is drawn; no-feasible probabilities and paired question intervals are also released. This development diagnostic compares final draws only: QAOA additionally performs angle training with up to 64 exact-expectation evaluations, whereas uniform feasible sampling does not. The same 20 questions recur across sizes, so the four size groups are not independent replications.",
        "",
        "![Figure 3. Optimum coverage from trained ideal distributions and uniform feasible draws. These development-derived probabilities describe the full objective, not answer correctness.](figures/sampling_coverage.png)",
        "",
    ]
    content = "\n".join(lines)
    atomic_text(
        output / "sampling_coverage.md", content.replace("](figures/", "](../figures/")
    )
    paper = Path("paper/manuscript.md")
    atomic_text(paper, replace_block(paper.read_text(), "SAMPLING", content))
    print("Analyzed 480 circuit solves across 20 development questions")


if __name__ == "__main__":
    main()
