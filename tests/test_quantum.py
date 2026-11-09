import importlib.util
import unittest
import numpy as np
from qrag.optimization import SelectionProblem


@unittest.skipUnless(importlib.util.find_spec('qiskit'), 'optional Qiskit not installed')
class QuantumTests(unittest.TestCase):
    def test_ising_spectrum_and_bit_order(self):
        from qrag.quantum import ising_coefficients,diagonal_energies
        rng=np.random.default_rng(9)
        for n in range(1,6):
            linear=rng.normal(size=n);pairs=np.triu(rng.normal(size=(n,n)),1)
            energies,bits=diagonal_energies(linear,pairs)
            c,h,j=ising_coefficients(linear,pairs)
            spins=1-2*bits
            mapped=c+spins@h+np.einsum('bi,ij,bj->b',spins,j,spins)
            np.testing.assert_allclose(energies,mapped,atol=1e-12)
            self.assertEqual(bits[1,0],1)
            if n>1:self.assertEqual(bits[1,1],0)

    def test_xy_mixer_preserves_count_and_penalty_ground_feasible(self):
        from qrag.quantum import qaoa_circuit,encoded_coefficients,diagonal_energies
        from qiskit.quantum_info import Statevector
        p=SelectionProblem(np.array([-.8,-.4,-.6,-.2]),np.triu(np.full((4,4),.1),1),2)
        qc,_=qaoa_circuit(p,[.4,.8,.2,.6],p=2,mixer='xy')
        probabilities=Statevector(qc).probabilities()
        linear,pairs,offset,_=encoded_coefficients(p,'penalty')
        energies,bits=diagonal_energies(linear,pairs)
        self.assertAlmostEqual(probabilities[np.sum(bits,axis=1)!=2].sum(),0,places=12)
        self.assertEqual(bits[np.argmin(energies+offset)].sum(),2)

    def test_actual_sampling_and_resources(self):
        from qrag.quantum import solve_qaoa
        p=SelectionProblem(np.array([-1.,-.7,-.4]),np.zeros((3,3)),1)
        result,resources=solve_qaoa(p,shots=64,max_evals=8)
        p.validate_selection(result.indices)
        self.assertEqual(resources['feasible_fraction'],1)
        self.assertFalse(result.optimal)
        self.assertGreater(resources['line']['two_qubit_gates'],0)
        self.assertEqual(sum(resources['sampled_counts'].values()),64)


if __name__=='__main__':
    unittest.main()
