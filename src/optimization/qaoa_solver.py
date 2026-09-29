"""
QAOA Solver Module

Uses Qiskit's Quantum Approximate Optimization Algorithm to solve the QUBO.
This acts as our "Quantum Document Selector".
"""

from qiskit.primitives import StatevectorSampler
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization.algorithms import MinimumEigenOptimizer
import time

class QAOASolver:
    """
    Wraps the Qiskit QAOA workflow for solving Quadratic Programs.
    """
    
    def __init__(self, reps=1, maxiter=50):
        """
        Initialize the quantum solver.
        
        Args:
            reps (int): The number of layers (depth) of the QAOA quantum circuit.
                        Higher reps = more accurate, but much slower to simulate.
                        reps=1 is a standard baseline.
            maxiter (int): Maximum number of iterations for the classical optimizer.
                           How many times the classical computer is allowed to 
                           tweak the quantum circuit's angles.
        """
        self.reps = reps
        self.maxiter = maxiter
        
        # 1. The Classical Optimizer (COBYLA is standard for QAOA)
        self.classical_optimizer = COBYLA(maxiter=self.maxiter)
        
        # 2. The Quantum Primitive (Sampler simulates the quantum measurements)
        # By default, this uses a local classical simulation of a quantum state.
        self.sampler = StatevectorSampler()
        
        # 3. The QAOA Algorithm
        self.qaoa = QAOA(
            sampler=self.sampler,
            optimizer=self.classical_optimizer,
            reps=self.reps
        )
        
        # 4. The Qiskit Optimization Wrapper
        # This takes our QUBO (QuadraticProgram) and feeds it to QAOA
        self.eigen_optimizer = MinimumEigenOptimizer(self.qaoa)

    def solve(self, qp):
        """
        Solve the given Quadratic Program using QAOA.
        
        Args:
            qp (QuadraticProgram): The math problem from qubo_builder.py
            
        Returns:
            dict containing:
                - selection_vector: list of 0s and 1s representing chosen docs
                - optimal_value: the final minimized score
                - time_taken: how long the quantum simulation took (seconds)
        """
        print(f"  [QAOA] Starting quantum optimization (reps={self.reps})...")
        start_time = time.time()
        
        # This is where the magic happens!
        result = self.eigen_optimizer.solve(qp)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"  [QAOA] Solved in {duration:.2f} seconds.")
        
        return {
            "selection_vector": result.x,
            "optimal_value": result.fval,
            "time_taken": duration
        }
