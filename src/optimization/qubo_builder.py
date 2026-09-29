"""
QUBO Builder Module

Translates the retrieval scores (relevance) and redundancy matrix (similarity)
into a Quadratic Unconstrained Binary Optimization (QUBO) problem.
This mathematical formulation is what the quantum algorithm (QAOA) will solve.
"""

from qiskit_optimization import QuadraticProgram
import numpy as np

class QUBORetriever:
    """
    Builds and manages the QUBO formulation for document selection.
    """
    
    def __init__(self, alpha=1.0, beta=0.5):
        """
        Initialize the QUBO builder.
        
        Args:
            alpha (float): Weight for the relevance term (linear).
                           Higher alpha = prefer relevant documents more.
            beta (float): Weight for the redundancy penalty (quadratic).
                          Higher beta = penalize similar documents more.
                          
        Tuning alpha and beta is crucial. If beta is too high, the optimizer
        might select irrelevant documents just because they are unique!
        """
        self.alpha = alpha
        self.beta = beta

    def build_qubo(self, relevance_scores, pairwise_similarity):
        """
        Constructs the QuadraticProgram for Qiskit to solve.
        
        Objective to MINIMIZE:
            -alpha * sum(r_i * x_i)  +  beta * sum(S_ij * x_i * x_j)
            
        Args:
            relevance_scores: numpy array of shape (N,)
            pairwise_similarity: numpy array of shape (N, N)
            
        Returns:
            QuadraticProgram object ready for quantum optimization.
        """
        num_docs = len(relevance_scores)
        
        # 1. Initialize an empty Quadratic Program
        qp = QuadraticProgram(name="Q-RAG Document Selection")
        
        # 2. Add binary variables (qubits) - one for each candidate document
        for i in range(num_docs):
            qp.binary_var(name=f"x_{i}")
            
        # 3. Build the Linear term: -alpha * relevance
        # We negate it because Qiskit MINIMIZES by default, 
        # and we want to MAXIMIZE relevance.
        linear_terms = {}
        for i in range(num_docs):
            # If r_i is high, we want this term to be very negative
            # so the optimizer is encouraged to set x_i = 1
            linear_terms[f"x_{i}"] = -self.alpha * relevance_scores[i]
            
        # 4. Build the Quadratic term: +beta * redundancy
        # We only look at upper triangle (i < j) to avoid double counting
        quadratic_terms = {}
        for i in range(num_docs):
            for j in range(i + 1, num_docs):
                sim = pairwise_similarity[i][j]
                
                # We only penalize if they are somewhat similar (similarity > 0)
                # No need to penalize documents that are already different.
                if sim > 0:
                    quadratic_terms[(f"x_{i}", f"x_{j}")] = self.beta * sim
                    
        # 5. Set the objective function
        qp.minimize(linear=linear_terms, quadratic=quadratic_terms)
        
        return qp

    def extract_solution(self, result_vector, documents):
        """
        Takes the binary string output from the quantum solver and maps it
        back to the actual documents.
        
        Args:
            result_vector: list/array of 0s and 1s (e.g., [1, 0, 1, 0...])
            documents: original list of candidate document dictionaries
            
        Returns:
            List of the selected document dictionaries.
        """
        selected_docs = []
        for i, bit in enumerate(result_vector):
            # Check if the variable was set to 1
            if bit > 0.5:  # Using >0.5 handles minor floating point errors
                selected_docs.append(documents[i])
                
        return selected_docs
