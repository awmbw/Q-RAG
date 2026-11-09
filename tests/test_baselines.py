"""Offline checks for experimental and mathematical contracts, not model quality."""

from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
from scipy.optimize import OptimizeResult

from qrag.config import ExperimentConfig, load_config
from qrag.data import adapt_example, load_examples
from qrag.experiments.run import run_experiment
from qrag.metrics import answer_metrics, evidence_metrics, normalize_answer
from qrag.optimization import (
    SelectionProblem, build_problem, select_exhaustive, select_milp, select_top_k,
)


def example() -> dict:
    return {
        "id": "q1", "question": "Where was the director born?", "answer": "India",
        "documents": [
            {"title": "Film", "text": "Film A was directed by Maya Rao.", "is_relevant": True},
            {"title": "Director", "text": "Maya Rao was born in India.", "is_relevant": True},
            {"title": "Release", "text": "Film A was released in 2010.", "is_relevant": False},
        ],
        "supporting_facts": {"titles": ["Film", "Director"]},
    }


class MetricTests(unittest.TestCase):
    def test_official_answer_semantics(self):
        # Expected values checked against HotpotQA's reference normalization/F1 rules.
        fixtures = [
            ("The United States.", "United States", 1.0, 1.0),
            ("red red blue", "red blue blue", 0.0, 2 / 3),
            ("India and Nepal", "India", 0.0, 0.5),
            ("yes indeed", "yes", 0.0, 0.0),
            ("no", "no answer", 0.0, 0.0),
            ("noanswer", "noanswer", 1.0, 1.0),
            ("", "", 1.0, 0.0),
            ("2010", "2011", 0.0, 0.0),
        ]
        for prediction, gold, em, f1 in fixtures:
            with self.subTest(prediction=prediction, gold=gold):
                scores = answer_metrics(prediction, gold)
                self.assertEqual(scores["answer_em"], em)
                self.assertAlmostEqual(scores["answer_f1"], f1)
        self.assertEqual(normalize_answer("  An EXAMPLE!  "), "example")

    def test_document_metrics_are_not_answer_metrics(self):
        query, labels = adapt_example(example())
        scores = evidence_metrics(query.documents[:1], labels)
        self.assertEqual(scores["document_recall"], 0.5)
        self.assertEqual(scores["document_precision"], 1.0)
        self.assertEqual(scores["all_supporting_documents"], 0.0)


class BoundaryTests(unittest.TestCase):
    def test_gold_changes_do_not_change_inference_input(self):
        first = example()
        second = example()
        second["answer"] = "Different answer"
        second["supporting_facts"]["titles"] = ["Release"]
        for doc in second["documents"]:
            doc["is_relevant"] = not doc["is_relevant"]
        query_a, labels_a = adapt_example(first)
        query_b, labels_b = adapt_example(second)
        self.assertEqual(query_a, query_b)
        self.assertNotEqual(labels_a, labels_b)
        self.assertFalse(hasattr(query_a, "answer"))
        self.assertFalse(hasattr(query_a.documents[0], "is_relevant"))

    def test_duplicate_titles_and_question_ids_rejected(self):
        raw = example()
        raw["documents"][1]["title"] = "Film"
        with self.assertRaisesRegex(ValueError, "duplicate document"):
            adapt_example(raw)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps([example(), example()]))
            with self.assertRaisesRegex(ValueError, "duplicate question"):
                load_examples(path)


class OptimizationTests(unittest.TestCase):
    def test_milp_matches_exhaustive_for_signed_pairs_and_k_boundaries(self):
        rng = np.random.default_rng(13)
        for n in range(1, 8):
            for k in sorted({0, n // 2, n}):
                with self.subTest(n=n, k=k):
                    problem = SelectionProblem(
                        rng.normal(size=n), np.triu(rng.normal(size=(n, n)), 1), k,
                    )
                    exact, mip = select_exhaustive(problem), select_milp(problem)
                    self.assertTrue(mip.optimal)
                    problem.validate_selection(mip.indices)
                    self.assertAlmostEqual(mip.energy, exact.energy, places=7)
                    if mip.lower_bound is not None:
                        self.assertAlmostEqual(mip.lower_bound, exact.energy, places=7)

    def test_zero_pair_problem_and_stable_ranking(self):
        relevance = np.array([0.8, 0.8, 0.3])
        problem = build_problem(relevance, np.eye(3), k=2)
        self.assertEqual(select_top_k(problem, relevance).indices, (0, 1))
        self.assertAlmostEqual(select_milp(problem).energy, -1.6)

    def test_redundancy_changes_selection_without_changing_count(self):
        relevance = np.array([1.0, 0.9, 0.8])
        similarities = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 1]])
        problem = build_problem(relevance, similarities, 2, beta=0.5)
        self.assertEqual(select_top_k(problem, relevance).indices, (0, 1))
        self.assertEqual(select_milp(problem).indices, (0, 2))
        self.assertAlmostEqual(problem.energy((0, 1)), -1.4)
        self.assertAlmostEqual(problem.energy((0, 2)), -1.8)

    def test_invalid_coefficients_and_selections_rejected(self):
        with self.assertRaises(ValueError):
            SelectionProblem(np.array([np.nan]), np.zeros((1, 1)), 1)
        with self.assertRaises(ValueError):
            SelectionProblem(np.ones(2), np.ones((2, 2)), 1)
        problem = SelectionProblem(np.ones(2), np.zeros((2, 2)), 1)
        for invalid in ((0, 0), (), (-1,), (2,)):
            with self.assertRaises(ValueError):
                problem.energy(invalid)

    def test_limit_incumbent_does_not_claim_optimality(self):
        problem = SelectionProblem(np.array([-1.0, -0.5]), np.zeros((2, 2)), 1)
        with patch("qrag.optimization.milp", return_value=OptimizeResult(
            status=1, x=np.array([1.0, 0]), message="Time limit",
            mip_dual_bound=-2.0, mip_gap=1.0,
        )):
            result = select_milp(problem)
        self.assertEqual(result.indices, (0,))
        self.assertEqual(result.status, "limit")
        self.assertFalse(result.optimal)

    def test_limit_without_incumbent_and_fractional_result(self):
        problem = SelectionProblem(np.array([-1.0, -0.5]), np.zeros((2, 2)), 1)
        with patch("qrag.optimization.milp", return_value=OptimizeResult(
            status=1, x=None, message="Time limit",
        )):
            self.assertIsNone(select_milp(problem).indices)
        with patch("qrag.optimization.milp", return_value=OptimizeResult(
            status=1, x=np.array([0.5, 0.5]), message="Invalid incumbent",
        )):
            with self.assertRaisesRegex(RuntimeError, "nonintegral"):
                select_milp(problem)


class ConfigTests(unittest.TestCase):
    def test_unknown_keys_and_invalid_values_fail(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text("limti = 3\n")
            with self.assertRaisesRegex(ValueError, "Unknown"):
                load_config(path)
        for changes in ({"k": 0}, {"k": True}, {"seed": -1}, {"beta": float("nan")},
                        {"generator_revision": "main"}, {"device": "gpu"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ExperimentConfig(**changes)


class FakeBackend:
    """Explicit test double, never an option in the research CLI."""
    def __init__(self, *, fail_generation=False, fail_prepare=False):
        self.prepared = self.scored = self.generated = 0
        self.fail_generation = fail_generation
        self.fail_prepare = fail_prepare

    def describe(self):
        return {"kind": "offline_test_double"}

    def prepare(self):
        self.prepared += 1
        if self.fail_prepare:
            raise RuntimeError("Test startup failure")
        return {"model_load_seconds": 0.0}

    def score(self, query):
        self.scored += 1
        return np.array([0.9, 0.8, 0.1]), np.eye(3), {"shared_feature_seconds": 0.0}

    def generate(self, query, selected):
        self.generated += 1
        if self.fail_generation:
            raise RuntimeError("Test generation failure")
        return {"answer": "India", "context_tokens": 20, "input_tokens": 50,
                "output_tokens": 1, "generation_seconds": 0.0, "prompt": "test fixture"}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        data = self.root / "data.json"
        data.write_text(json.dumps([example()]))
        self.config = ExperimentConfig(dataset=str(data), limit=1, k=2)
        self.output = self.root / "run"

    def run_quiet(self, *args, **kwargs):
        with redirect_stdout(io.StringIO()):
            return run_experiment(*args, **kwargs)

    def test_end_to_end_and_complete_resume_without_model_reload(self):
        backend = FakeBackend()
        summary = self.run_quiet(self.config, self.output, backend=backend)
        self.assertEqual(backend.scored, 1)  # Shared across both selectors.
        self.assertEqual(backend.generated, 2)
        self.assertEqual(summary["methods"]["milp"]["answer_em_all_questions"], 1.0)
        rows = (self.output / "predictions.jsonl").read_text().splitlines()
        self.assertEqual(len(rows), 2)
        next_backend = FakeBackend()
        self.run_quiet(self.config, self.output, resume=True, backend=next_backend)
        self.assertEqual(next_backend.prepared, 0)
        self.assertEqual(rows, (self.output / "predictions.jsonl").read_text().splitlines())

    def test_partial_resume_keeps_completed_record(self):
        self.run_quiet(self.config, self.output, backend=FakeBackend())
        path = self.output / "predictions.jsonl"
        first = path.read_text().splitlines()[0]
        path.write_text(first + "\n")  # Simulate interruption after one completed method.
        backend = FakeBackend()
        self.run_quiet(self.config, self.output, resume=True, backend=backend)
        self.assertEqual(backend.generated, 1)
        self.assertEqual(len(path.read_text().splitlines()), 2)
        self.assertEqual(path.read_text().splitlines()[0], first)

    def test_changed_config_and_changed_data_reject_resume(self):
        self.run_quiet(self.config, self.output, backend=FakeBackend())
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.run_quiet(replace(self.config, beta=0.8), self.output,
                           resume=True, backend=FakeBackend())
        data = example()
        data["answer"] = "Changed reference"
        Path(self.config.dataset).write_text(json.dumps([data]))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.run_quiet(self.config, self.output, resume=True, backend=FakeBackend())

    def test_failures_remain_in_answer_denominator(self):
        summary = self.run_quiet(self.config, self.output,
                                 backend=FakeBackend(fail_generation=True))
        for result in summary["methods"].values():
            self.assertEqual(result["questions"], 1)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(result["answer_f1_all_questions"], 0.0)
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "completed_with_errors")

    def test_startup_failure_is_recorded(self):
        with self.assertRaises(RuntimeError):
            self.run_quiet(self.config, self.output, backend=FakeBackend(fail_prepare=True))
        self.assertTrue((self.output / "failure.json").exists())
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "interrupted_or_failed")

    def test_explicit_short_pool_policy(self):
        self.run_quiet(replace(self.config, k=5), self.output, backend=FakeBackend())
        for line in (self.output / "predictions.jsonl").read_text().splitlines():
            record = json.loads(line)
            self.assertEqual(record["effective_k"], 3)
            self.assertEqual(record["selected_count"], 3)
        error_output = self.root / "error"
        summary = self.run_quiet(replace(self.config, k=5, short_pool_policy="error"),
                                 error_output, backend=FakeBackend())
        self.assertEqual(summary["methods"]["top_k"]["failed"], 1)


if __name__ == "__main__":
    unittest.main()
