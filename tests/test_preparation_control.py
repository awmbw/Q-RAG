"""Protect the mathematical diagnosis without changing the frozen quantum core."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepared_qaoa_study import prepared_circuit

from qrag.optimization import SelectionProblem
from qrag.quantum import diagonal_energies, qaoa_circuit


class PreparationControlTests(unittest.TestCase):
    def test_first_cost_phase_and_feasible_superposition(self):
        from qiskit.quantum_info import Statevector

        rng = np.random.default_rng(31)
        problem = SelectionProblem(
            rng.normal(size=6), np.triu(rng.normal(size=(6, 6)), 1), 3
        )
        original = [
            Statevector(qaoa_circuit(problem, [g, 0.61], seed=42)[0]).probabilities()
            for g in [0.1, 1.7]
        ]
        np.testing.assert_allclose(original[0], original[1], atol=1e-12)
        prepared = [
            Statevector(
                prepared_circuit(problem, [g, 0.61], seed=42)[0]
            ).probabilities()
            for g in [0.1, 1.7]
        ]
        self.assertGreater(np.max(np.abs(prepared[0] - prepared[1])), 1e-4)
        _, bits = diagonal_energies(problem.linear, problem.pairs)
        for probabilities in prepared:
            self.assertAlmostEqual(
                float(probabilities[bits.sum(axis=1) == 3].sum()), 1.0
            )


if __name__ == "__main__":
    unittest.main()
