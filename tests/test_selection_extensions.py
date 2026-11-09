import unittest

import numpy as np

from qrag.data import Document, QueryInput
from qrag.evidence import build_evidence, interaction_problem
from qrag.optimization import (
    SelectionProblem,
    select_annealing,
    select_exhaustive,
    select_greedy,
    select_milp,
    select_top_k,
)


class ExtendedSelectionTests(unittest.TestCase):
    def test_unicode_entity_surface_has_exact_provenance(self):
        query = QueryInput(
            "q",
            "Where is Istanbul High School?",
            (
                Document(
                    "a", "Istanbul High School", "İstanbul High School is in Turkey."
                ),
                Document("b", "Turkey", "Istanbul High School is a school."),
            ),
        )
        comp, coverage, graph = build_evidence(query, np.array([0.8, 0.6]))
        self.assertGreater(comp[0, 1], 0)
        for doc in query.documents:
            for mention in graph["mentions"][doc.id]:
                self.assertEqual(
                    doc.text[mention["start"] : mention["end"]], mention["surface"]
                )

    def test_budget_milp_matches_oracle_with_negative_pairs(self):
        rng = np.random.default_rng(55)
        for n in range(2, 8):
            for budget in (0, 3, 8):
                problem = SelectionProblem(
                    rng.normal(size=n),
                    np.triu(rng.normal(size=(n, n)), 1),
                    None,
                    rng.integers(1, 5, size=n),
                    budget,
                )
                exact = select_exhaustive(problem)
                mip = select_milp(problem)
                self.assertAlmostEqual(exact.energy, mip.energy, places=7)
                problem.validate_selection(mip.indices)

    def test_infeasible_budget_and_minimum(self):
        problem = SelectionProblem(
            np.array([-1.0, -0.8]),
            np.zeros((2, 2)),
            None,
            np.array([5, 6]),
            3,
            min_count=1,
        )
        self.assertIsNone(select_milp(problem).indices)
        self.assertIsNone(select_exhaustive(problem).indices)

    def test_heuristics_feasible_and_seeded(self):
        p = SelectionProblem(
            np.array([-0.8, -0.7, -0.6, -0.5]), np.triu(np.ones((4, 4)) * 0.2, 1), 2
        )
        a = select_annealing(p, seed=7, steps=100)
        b = select_annealing(p, seed=7, steps=100)
        self.assertEqual(a.indices, b.indices)
        p.validate_selection(select_greedy(p).indices)
        self.assertLessEqual(a.energy, select_top_k(p, -p.linear).energy)

    def test_graph_spans_and_label_free_features(self):
        q = QueryInput(
            "q",
            "Where was Maya Rao born?",
            (
                Document("a", "Film A", "Film A was directed by Maya Rao."),
                Document("b", "Maya Rao", "Maya Rao was born in India."),
            ),
        )
        comp, coverage, graph = build_evidence(q, np.array([0.8, 0.7]))
        self.assertGreater(comp[0, 1], 0)
        self.assertTrue(graph["edges"])
        for doc in q.documents:
            for mention in graph["mentions"][doc.id]:
                self.assertEqual(
                    doc.text[mention["start"] : mention["end"]].casefold(),
                    mention["entity"],
                )
        p = interaction_problem(np.array([0.8, 0.7]), np.eye(2), 2, 1.0, comp)
        self.assertLess(p.pairs[0, 1], 0)


if __name__ == "__main__":
    unittest.main()
