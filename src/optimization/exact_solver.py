"""
Exact Classical Solver Module

Since simulating QAOA is slow (5+ minutes per query), we use this classical
exact solver for rapid hyperparameter tuning over thousands of questions.
It perfectly mimics what a flawless Quantum Computer would output, but 
does it in milliseconds by directly computing the lowest energy state.
"""

from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_optimization.algorithms import MinimumEigenOptimizer
import time

class ExactSolver:
    """
    Wraps the Qiskit NumPy Minimum Eigensolver.
    """
    
    def __init__(self):
        # The classical exact eigensolver
        self.exact_mes = NumPyMinimumEigensolver()
        
        # The Qiskit Optimization Wrapper
        self.eigen_optimizer = MinimumEigenOptimizer(self.exact_mes)

    def solve(self, qp):
        """
        Solve the given Quadratic Program classically and exactly.
        
        Args:
            qp (QuadraticProgram): The math problem from qubo_builder.py
            
        Returns:
            dict containing:
                - selection_vector: list of 0s and 1s representing chosen docs
                - optimal_value: the final minimized score
                - time_taken: how long it took (seconds)
        """
        start_time = time.time()
        
        # Solve it instantly
        result = self.eigen_optimizer.solve(qp)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "selection_vector": result.x,
            "optimal_value": result.fval,
            "time_taken": duration
        }
