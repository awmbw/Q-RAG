import importlib.util
import sqlite3
import time
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

AVAILABLE = (
    importlib.util.find_spec("fastapi") is not None
    and importlib.util.find_spec("httpx") is not None
)


class FakeEngine:
    ready = True

    def __init__(self, gate=None, fail=False):
        self.gate = gate
        self.fail = fail

    def execute(self, request, job_id):
        if self.gate is not None:
            self.gate.wait(3)
        if self.fail:
            raise TimeoutError("test bounded-stage deadline")
        return {"job_id": job_id, "wall_seconds": 0.01}

    def close(self):
        pass


@unittest.skipUnless(AVAILABLE, "optional service dependencies unavailable")
class ServiceTests(unittest.TestCase):
    def request(self):
        return {
            "question": "Where?",
            "sources": [{"id": "a", "title": "A", "text": "India."}],
            "k": 1,
        }

    def wait(self, client, job_id):
        for _ in range(200):
            result = client.get("/jobs/" + job_id).json()
            if result["status"] not in {"queued", "running"}:
                return result
            time.sleep(0.005)
        self.fail("Offline job did not finish")

    def test_job_lifecycle_dashboard_and_metrics(self):
        from fastapi.testclient import TestClient

        from qrag_service.app import create_app

        with (
            TemporaryDirectory() as directory,
            TestClient(
                create_app(FakeEngine(), Path(directory) / "jobs.sqlite")
            ) as client,
        ):
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/ready").status_code, 200)
            self.assertIn("Compare source selection", client.get("/").text)
            response = client.post("/jobs", json=self.request())
            self.assertEqual(response.status_code, 202)
            row = self.wait(client, response.json()["id"])
            self.assertEqual(row["status"], "completed")
            self.assertIsNotNone(row["queue_seconds"])
            self.assertEqual(
                client.get("/metrics").json()["jobs_by_status"]["completed"], 1
            )
            self.assertEqual(client.get("/jobs/absent").status_code, 404)

    def test_validation_and_bounded_queue(self):
        from fastapi.testclient import TestClient

        from qrag_service.app import create_app

        gate = Event()
        with (
            TemporaryDirectory() as directory,
            TestClient(
                create_app(
                    FakeEngine(gate), Path(directory) / "jobs.sqlite", capacity=1
                )
            ) as client,
        ):
            bad = {**self.request(), "answer": "gold"}
            self.assertEqual(client.post("/jobs", json=bad).status_code, 422)
            bad = self.request()
            bad["sources"][0]["is_relevant"] = True
            self.assertEqual(client.post("/jobs", json=bad).status_code, 422)
            try:
                first = client.post("/jobs", json=self.request())
                self.assertEqual(first.status_code, 202)
                self.assertEqual(
                    client.post("/jobs", json=self.request()).status_code, 429
                )
            finally:
                gate.set()

    def test_timeout_is_recorded(self):
        from fastapi.testclient import TestClient

        from qrag_service.app import create_app

        with (
            TemporaryDirectory() as directory,
            TestClient(
                create_app(FakeEngine(fail=True), Path(directory) / "jobs.sqlite")
            ) as client,
        ):
            job = client.post("/jobs", json=self.request()).json()
            self.assertEqual(self.wait(client, job["id"])["status"], "timed_out")

    def test_explicit_quantum_fallback(self):
        from qrag_service.engine import Engine
        from qrag_service.schemas import CompareRequest

        request = CompareRequest(**{**self.request(), "methods": ["qaoa"]})
        with TemporaryDirectory() as directory:
            engine = Engine(Path(directory))
            engine.ready = True
            engine.encoder = SimpleNamespace(
                score=lambda q: (np.array([0.8]), np.eye(1), {})
            )
            engine.model = SimpleNamespace(
                device="cpu",
                config=SimpleNamespace(
                    generator_model="test",
                    generator_revision="test",
                    generator_dtype="float32",
                ),
                generate=lambda q, s: {
                    "answer": "India",
                    "context_tokens": 2,
                    "input_tokens": 10,
                    "generation_seconds": 0.01,
                },
            )
            with (
                patch(
                    "qrag_service.engine.cached_evidence",
                    return_value=(np.zeros((1, 1)), np.ones((1, 1)), {}),
                ),
                patch(
                    "qrag_service.engine.solve_qaoa",
                    side_effect=RuntimeError("test quantum failure"),
                ),
            ):
                result = engine.execute(request, "job")
                self.assertEqual(result["results"][0]["actual_method"], "milp")
                self.assertTrue(result["results"][0]["fallback"]["used"])
                with self.assertRaises(RuntimeError):
                    engine.execute(
                        request.model_copy(update={"allow_classical_fallback": False}),
                        "job",
                    )


class PersistenceTests(unittest.TestCase):
    def test_restart_marks_abandoned_jobs(self):
        from qrag_service.jobs import Jobs

        with TemporaryDirectory() as directory:
            path = Path(directory) / "jobs.sqlite"
            manager = Jobs(FakeEngine(), path)
            manager.close()
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                    ("old", "running", 0, 1, None, "{}", None, None),
                )
            restarted = Jobs(FakeEngine(), path)
            self.assertEqual(restarted.get("old")["status"], "interrupted")
            restarted.close()


if __name__ == "__main__":
    unittest.main()
