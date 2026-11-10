"""Draw the implemented pipeline and its reference-annotation boundary."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from figure_export import save_figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def main():
    fig, axis = plt.subplots(figsize=(7.4, 3.1))
    axis.set_xlim(0, 9)
    axis.set_ylim(-0.05, 3)
    axis.axis("off")
    xs = [0.15, 2.4, 4.65, 6.9]

    def box(x, y, text, color):
        axis.add_patch(
            FancyBboxPatch(
                (x, y),
                1.95,
                0.65,
                boxstyle="round,pad=0.04",
                linewidth=0.8,
                edgecolor="#455a64",
                facecolor=color,
            )
        )
        axis.text(
            x + 0.975,
            y + 0.325,
            text,
            ha="center",
            va="center",
            fontsize=8.4,
            linespacing=1.3,
        )

    def arrow(start, stop, color="#455a64", dashed=False):
        axis.add_patch(
            FancyArrowPatch(
                start,
                stop,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1,
                color=color,
                linestyle="--" if dashed else "-",
            )
        )

    top = [
        "Question + sources\nor bounded corpus",
        "Token-safe chunks\ncache + exact index",
        "One shared\ncandidate pool",
        "Relevance / redundancy\nentity-link coefficients",
    ]
    bottom = [
        "Journal + manifests\ntables + paper",
        "Answer / support scores\npaired comparisons",
        "Consistent context\nfixed Qwen generation",
        "MILP / heuristics / QAOA\ncount or token budget",
    ]
    for x, label in zip(xs, top):
        box(x, 2, label, "#e3f0e9")
    for x, label in zip(xs, bottom):
        box(x, 0.95, label, "#e8eff7")
    for left, right in zip(xs, xs[1:]):
        arrow((left + 1.99, 2.325), (right - 0.05, 2.325))
        arrow((right - 0.05, 1.275), (left + 1.99, 1.275))
    arrow((xs[-1] + 0.975, 1.97), (xs[-1] + 0.975, 1.64))
    axis.text(
        3.375,
        0.25,
        "Reference answers + support annotations",
        ha="center",
        fontsize=8.2,
        color="#9a4038",
    )
    arrow((3.375, 0.42), (3.375, 0.91), color="#9a4038", dashed=True)
    axis.text(
        7.85,
        0.25,
        "Reference labels enter evaluation only",
        ha="right",
        fontsize=8,
        color="#9a4038",
    )
    axis.text(0.15, 2.85, "Shared inference path", fontsize=9, color="#355b4a")
    fig.tight_layout(pad=0.5)
    output = Path("paper/figures")
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        save_figure(fig, output / ("architecture." + suffix))
    plt.close(fig)
    print("Rendered implemented pipeline and label-isolation boundary")


if __name__ == "__main__":
    main()
