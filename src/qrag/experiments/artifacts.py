"""Atomic artifacts and a strict resume identity, including uncommitted source."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def source_hash() -> str:
    root = Path(__file__).resolve().parents[1]
    return value_hash(
        {
            str(path.relative_to(root)): file_hash(path)
            for path in sorted(root.rglob("*.py"))
        }
    )


def environment() -> dict:
    versions = {}
    for name in (
        "numpy",
        "scipy",
        "torch",
        "transformers",
        "sentence-transformers",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
    }


def git_state() -> dict:
    def read(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "commit": read("rev-parse", "HEAD"),
        "status": read("status", "--short"),
        "tracked_diff_sha256": value_hash(read("diff", "HEAD")),
    }


def atomic_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(path: Path, value: object) -> None:
    atomic_text(
        path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


class RunStore:
    def __init__(self, directory: Path, identity: dict, resume: bool = False):
        self.directory = directory
        self.records: dict[tuple[str, str], dict] = {}
        manifest_path = directory / "manifest.json"
        identity_sha256 = value_hash(identity)
        if resume:
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if self.manifest["identity_sha256"] != identity_sha256:
                raise ValueError(
                    "Resume identity mismatch: code, config, data or runtime changed"
                )
            path = directory / "predictions.jsonl"
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    record = json.loads(line)
                    key = (record["question_id"], record["method"])
                    if key in self.records:
                        raise ValueError(f"Duplicate prediction record: {key}")
                    self.records[key] = record
        else:
            directory.mkdir(parents=True, exist_ok=False)
            self.manifest = {
                "manifest_version": 1,
                "created_at": utc_now(),
                "identity": identity,
                "identity_sha256": identity_sha256,
                "git": git_state(),
                "status": "created",
                "invocations": [],
            }
            write_json(manifest_path, self.manifest)

    def save_manifest(self) -> None:
        write_json(self.directory / "manifest.json", self.manifest)

    def save_record(self, record: dict) -> None:
        key = (record["question_id"], record["method"])
        if key in self.records:
            raise ValueError(f"Record already exists: {key}")
        self.records[key] = record
        atomic_text(
            self.directory / "predictions.jsonl",
            "".join(
                json.dumps(item, sort_keys=True, allow_nan=False) + "\n"
                for item in self.records.values()
            ),
        )
