"""Bounded one-worker execution and restart-aware SQLite job metadata."""

import fcntl
import json
import logging
import sqlite3
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import BoundedSemaphore, RLock

LOGGER = logging.getLogger("qrag.jobs")


class QueueFull(Exception):
    pass


class Jobs:
    def __init__(self, engine, database: Path, capacity=4):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.writer_lock = database.with_suffix(database.suffix + ".lock").open("a")
        try:
            fcntl.flock(self.writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.writer_lock.close()
            raise RuntimeError(
                "Another service worker is using this job database; run one worker"
            ) from exc
        self.engine = engine
        self.db = sqlite3.connect(database, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT, created REAL, started REAL, ended REAL, payload TEXT, result TEXT, error TEXT)"
        )
        self.db.execute(
            "UPDATE jobs SET status='interrupted', ended=? WHERE status IN ('queued','running')",
            (time.time(),),
        )
        self.db.commit()
        self.lock = RLock()
        self.slots = BoundedSemaphore(capacity)
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="qrag-inference"
        )
        self.closed = False

    def submit(self, request):
        if self.closed:
            raise RuntimeError("Service is shutting down")
        if not self.slots.acquire(blocking=False):
            raise QueueFull("Inference queue is full; retry after a job completes")
        job_id = uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                (
                    job_id,
                    "queued",
                    time.time(),
                    None,
                    None,
                    request.model_dump_json(),
                    None,
                    None,
                ),
            )
            # Keep the newest 200 terminal jobs; never prune queued/running work.
            self.db.execute(
                "DELETE FROM jobs WHERE id IN (SELECT id FROM jobs WHERE status NOT IN ('queued','running') ORDER BY created DESC LIMIT -1 OFFSET 200)"
            )
        try:
            self.executor.submit(self._execute, job_id, request)
        except Exception:
            self.slots.release()
            raise
        return job_id

    def _execute(self, job_id, request):
        with self.lock, self.db:
            self.db.execute(
                "UPDATE jobs SET status='running',started=? WHERE id=?",
                (time.time(), job_id),
            )
        try:
            result = self.engine.execute(request, job_id)
            with self.lock, self.db:
                self.db.execute(
                    "UPDATE jobs SET status='completed',ended=?,result=? WHERE id=?",
                    (time.time(), json.dumps(result, allow_nan=False), job_id),
                )
            LOGGER.info(
                json.dumps(
                    {
                        "event": "job.completed",
                        "job_id": job_id,
                        "wall_seconds": result.get("wall_seconds"),
                    }
                )
            )
        except Exception as exc:
            status = "timed_out" if isinstance(exc, TimeoutError) else "failed"
            error = {"type": type(exc).__name__, "message": str(exc)[:500]}
            with self.lock, self.db:
                self.db.execute(
                    "UPDATE jobs SET status=?,ended=?,error=? WHERE id=?",
                    (status, time.time(), json.dumps(error), job_id),
                )
            LOGGER.warning(
                json.dumps(
                    {
                        "event": "job." + status,
                        "job_id": job_id,
                        "error_type": type(exc).__name__,
                    }
                )
            )
        finally:
            self.slots.release()

    def get(self, job_id):
        with self.lock:
            row = self.db.execute(
                "SELECT id,status,created,started,ended,result,error FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "status": row[1],
            "created_at_unix": row[2],
            "started_at_unix": row[3],
            "ended_at_unix": row[4],
            "queue_seconds": row[3] - row[2] if row[3] else None,
            "total_seconds": row[4] - row[2] if row[4] else None,
            "result": json.loads(row[5]) if row[5] else None,
            "error": json.loads(row[6]) if row[6] else None,
        }

    def metrics(self):
        with self.lock:
            rows = self.db.execute(
                "SELECT status,created,started,ended FROM jobs"
            ).fetchall()
        durations = sorted(
            end - start
            for status, created, start, end in rows
            if status == "completed" and start and end
        )

        def percentile(q):
            if not durations:
                return None
            position = (len(durations) - 1) * q
            low = int(position)
            high = min(low + 1, len(durations) - 1)
            return durations[low] + (durations[high] - durations[low]) * (
                position - low
            )

        return {
            "jobs_by_status": {
                s: sum(row[0] == s for row in rows)
                for s in sorted({row[0] for row in rows})
            },
            "completed_service_seconds_p50": percentile(0.5),
            "completed_service_seconds_p95": percentile(0.95),
            "latency_scope": "retained completed jobs; execution includes cold preparation if needed; queue time reported per job",
        }

    def close(self):
        self.closed = True
        self.executor.shutdown(wait=True, cancel_futures=False)
        self.engine.close()
        self.db.close()
        fcntl.flock(self.writer_lock, fcntl.LOCK_UN)
        self.writer_lock.close()
