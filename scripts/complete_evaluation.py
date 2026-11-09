"""Finish declared secondary controls and audits after the primary matrix completes."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def primary_complete():
    entries = json.loads(Path("configs/final_matrix.json").read_text())["configs"]
    for entry in entries:
        path = Path("results") / Path(entry["config"]).stem / "manifest.json"
        if not path.exists():
            return False
        status = json.loads(path.read_text())["status"]
        if status not in {"completed", "completed_with_errors"}:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-for-primary", action="store_true")
    args = parser.parse_args()
    if args.wait_for_primary:
        while not primary_complete():
            time.sleep(30)
    if not primary_complete():
        raise ValueError(
            "Primary matrix is incomplete; scientific source must remain frozen"
        )
    commands = [
        ["scripts/run_matrix.py", "--matrix", "configs/formulation_controls.json"],
        ["scripts/gate_budget_study.py"],
        [
            "scripts/prepared_qaoa_study.py",
            "--config",
            "configs/secondary/final_hotpotqa_prepared.json",
        ],
        [
            "scripts/prepared_qaoa_study.py",
            "--config",
            "configs/secondary/final_musique_prepared.json",
        ],
        ["scripts/audit_final_runs.py"],
        ["scripts/error_analysis.py"],
        ["scripts/assemble_results.py"],
        ["scripts/analyze_sampling_coverage.py"],
        ["scripts/reproduce_public_tables.py", "--verify"],
    ]
    environment = {
        **os.environ,
        "HF_HUB_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
    }
    for command in commands:
        name = Path(command[0]).stem
        print("Starting", name, flush=True)
        with (Path("results") / (name + "_completion.log")).open("a") as log:
            result = subprocess.run(
                [sys.executable, *command],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        if result.returncode:
            raise SystemExit(f"{name} failed; inspect results/{name}_completion.log")
        print("Completed", name, flush=True)


if __name__ == "__main__":
    main()
