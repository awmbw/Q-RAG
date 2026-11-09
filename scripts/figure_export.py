"""Stable SVG identifiers and clean source whitespace for publication figures."""

import matplotlib


def save_figure(figure, path):
    matplotlib.rcParams["svg.hashsalt"] = "qrag-research-20261110"
    options = {"metadata": {"Date": None}} if path.suffix == ".svg" else {}
    figure.savefig(path, dpi=240, bbox_inches="tight", **options)
    if path.suffix == ".svg":
        path.write_text(
            "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
        )
