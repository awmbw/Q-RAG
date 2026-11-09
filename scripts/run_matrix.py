"""Run recorded configurations sequentially without competing for GPU memory."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs", type=Path, nargs="+")
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--root", type=Path, default=Path("results"))
    args = parser.parse_args()
    if bool(args.configs) == bool(args.matrix):
        parser.error("Supply either --configs or --matrix")
    expected = {}
    if args.matrix:
        entries = json.loads(args.matrix.read_text())["configs"]
        args.configs = [Path(entry["config"]) for entry in entries]
        expected = {entry["config"]: entry["sha256"] for entry in entries}
    args.root.mkdir(parents=True, exist_ok=True)
    failures = []
    for config in args.configs:
        if (
            expected
            and hashlib.sha256(config.read_bytes()).hexdigest() != expected[str(config)]
        ):
            raise ValueError("Frozen configuration changed: " + str(config))
        directory = args.root / config.stem
        command = [
            sys.executable,
            "-m",
            "qrag.experiments.study",
            "--config",
            str(config),
            "--output",
            str(directory),
        ]
        if directory.exists():
            command.append("--resume")
        print("Starting", config, flush=True)
        with (args.root / (config.stem + ".log")).open("a") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        print("Finished", config, "exit", result.returncode, flush=True)
        if result.returncode:
            failures.append(config.name)
    if failures:
        raise SystemExit("Runs with errors: " + ", ".join(failures))


if __name__ == "__main__":
    main()
