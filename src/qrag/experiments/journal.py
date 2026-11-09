"""Append/fsync experiment journal with validated retry and torn-tail recovery."""

import json
import os
from pathlib import Path

from qrag.experiments.artifacts import RunStore, value_hash


class JournalRunStore(RunStore):
    def __init__(self, directory: Path, identity: dict, resume=False):
        if not resume:
            super().__init__(directory, identity, False)
            self.manifest["storage"] = "append_fsync_jsonl_v2"
            self.save_manifest()
            return
        self.directory = directory
        self.manifest = json.loads((directory / "manifest.json").read_text())
        if self.manifest["identity_sha256"] != value_hash(identity):
            raise ValueError(
                "Resume identity mismatch: code, config, data or runtime changed"
            )
        path = directory / "predictions.jsonl"
        data = path.read_bytes() if path.exists() else b""
        if data and not data.endswith(b"\n"):
            boundary = data.rfind(b"\n") + 1
            tail = data[boundary:]
            try:
                json.loads(tail)
            except (ValueError, UnicodeDecodeError):
                # Keep the interrupted bytes for audit, then safely recompute
                # that unfinished record. Identity was checked before mutation.
                with (directory / "recovered_partial_tail.bin").open("ab") as handle:
                    handle.write(tail)
                with path.open("r+b") as handle:
                    handle.truncate(boundary)
                    handle.flush()
                    os.fsync(handle.fileno())
                data = data[:boundary]
                self.manifest.setdefault("recoveries", []).append(
                    {"partial_bytes": len(tail)}
                )
            else:
                with path.open("ab") as handle:
                    handle.write(b"\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                data += b"\n"
        self.records = {}
        for line in data.splitlines():
            record = json.loads(line)
            key = (record["question_id"], record["method"])
            previous = self.records.get(key)
            if previous is not None and (
                previous["status"] == "success"
                or record.get("attempt") != previous.get("attempt", 1) + 1
            ):
                raise ValueError("Invalid duplicate/retry record")
            self.records[key] = record

    def save_record(self, record):
        key = (record["question_id"], record["method"])
        previous = self.records.get(key)
        if previous and previous["status"] == "success":
            raise ValueError("Successful record already exists")
        record = {
            **record,
            "attempt": previous.get("attempt", 1) + 1 if previous else 1,
        }
        payload = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
        with (self.directory / "predictions.jsonl").open("ab") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.records[key] = record
