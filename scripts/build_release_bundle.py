"""Package a clean committed research artifact without weights or private files."""

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from qrag.experiments.artifacts import atomic_text, file_hash, source_hash, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v0.1.0-research")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit the reviewed artifact before packaging")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    out = args.output or Path("results/release") / args.version
    out.mkdir(parents=True, exist_ok=False)
    evidence = Path("docs/research_report/evidence")
    audit = json.loads((evidence / "final_audit.json").read_text())
    assert audit["total_latest_records"] == 53230 and len(audit["runs"]) == 24
    assert source_hash() == audit["common_source_sha256"]
    public_runs = 0
    for path in evidence.glob("final_*.json"):
        meta = json.loads(path.read_text())
        if "compact_predictions_file" in meta:
            assert (
                file_hash(evidence / meta["compact_predictions_file"])
                == meta["compact_predictions_sha256"]
            )
            public_runs += 1
    assert public_runs == 24
    qa = json.loads((evidence / "manuscript_export_qa.json").read_text())
    assert file_hash(Path(qa["pdf"])) == qa["sha256"]
    assert file_hash(Path("paper/manuscript.md")) == qa["manuscript_sha256"]
    assert qa["visually_inspected_pages"] == list(range(1, qa["pages"] + 1))
    source_archive = out / f"qrag-research-{args.version}.zip"
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            "--prefix=qrag-research/",
            f"--output={source_archive}",
            "HEAD",
        ],
        check=True,
    )
    with zipfile.ZipFile(source_archive) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        for forbidden in [
            "docs/LEARNING_LOG.md",
            "midsem_report.tex",
            ".env",
            "data/processed/",
            "data/raw/",
            "venv/",
            ".cache/",
            "models/",
            "checkpoints/",
        ]:
            assert not any(
                n == "qrag-research/" + forbidden
                or n.startswith("qrag-research/" + forbidden.rstrip("/") + "/")
                for n in names
            )
    wheels = sorted(Path("dist").glob("qrag_research-*.whl"))
    if len(wheels) != 1:
        raise ValueError("Build exactly one current wheel before release")
    with zipfile.ZipFile(wheels[0]) as archive:
        assert archive.testzip() is None
        assert "qrag_service/static/index.html" in archive.namelist()
    shutil.copy2(wheels[0], out / wheels[0].name)
    shutil.copy2(Path(qa["pdf"]), out / "manuscript.pdf")
    write_json(
        out / "release_manifest.json",
        {
            "version": args.version,
            "commit": commit,
            "scientific_source_sha256": source_hash(),
            "primary_records": 50290,
            "all_evaluation_records": 53230,
            "distinct_held_out_questions": 1000,
            "public_prediction_runs": public_runs,
            "pdf_pages": qa["pages"],
            "status": "Research artifact preview; manuscript not submitted or peer reviewed",
            "quantum_execution": "local simulation only",
            "project_license": "not yet assigned by rights holders",
            "excluded": "weights, raw/processed datasets, large local full runs, caches and private notes",
        },
    )
    notes = f"""Q-RAG {args.version} research artifact

Commit: {commit}

Contains the source/configuration/documentation/evidence archive, installable wheel, reviewed {qa["pages"]}-page manuscript PDF and checksums.

- 53,230 audited records across 24 conditions; 1,000 distinct held-out questions.
- Public table reconstruction and 110 model-free optimization instances.
- Actual simulated QAOA, classical references and local CPU/GPU engineering checks.
- The proposed evidence-guidance benefit is not established; no practical quantum advantage is claimed.

This is an artifact preview, not a scholarly publication or acceptance. Human scientific review, author/rights-holder decisions, independent graph annotation, venue formatting and submission remain external. Project-wide licensing has not been assigned. See docs/HUMAN_HANDOFF.md and docs/RIGHTS_AND_ATTRIBUTION.md in the source archive.
"""
    atomic_text(out / "RELEASE_NOTES.md", notes)
    files = sorted(p for p in out.iterdir() if p.is_file())
    atomic_text(
        out / "SHA256SUMS.txt", "".join(f"{file_hash(p)}  {p.name}\n" for p in files)
    )
    print("Packaged", commit, "into", out)


if __name__ == "__main__":
    main()
