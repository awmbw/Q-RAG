"""
Script 04: Test the QUBO formulation.
Goal: Verify that Qiskit correctly builds the mathematical optimization 
problem from our retriever's output.
"""

import json
import sys
import numpy as np

sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever
from src.optimization.qubo_builder import QUBORetriever

# ─────────────────────────────────────────────
# STEP 1: Load Data & Initialize Modules
# ─────────────────────────────────────────────
print("Loading data and models...")
with open("data/processed/dev_set.json", "r") as f:
    dev_data = json.load(f)

# Initialize both our modules
retriever = DenseRetriever()
# Let's use alpha=1.0 (relevance) and beta=0.5 (redundancy penalty)
qubo_builder = QUBORetriever(alpha=1.0, beta=0.5)

# ─────────────────────────────────────────────
# STEP 2: Get scores from the Retriever
# ─────────────────────────────────────────────
example = dev_data[0]
print(f"\nQuestion: {example['question']}")

result = retriever.retrieve(
    query=example["question"],
    documents=example["documents"]
)

# ─────────────────────────────────────────────
# STEP 3: Build the QUBO
# ─────────────────────────────────────────────
print("\nBuilding QUBO formulation...")
qp = qubo_builder.build_qubo(
    relevance_scores=result["relevance_scores"],
    pairwise_similarity=result["pairwise_similarity"]
)

# ─────────────────────────────────────────────
# STEP 4: Inspect the Mathematical Formulation
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("THE MATH PROBLEM (Qiskit's internal representation)")
print("=" * 70)

# Use the modern prettyprint method instead of export_as_lp_string
math_string = qp.prettyprint()
lines = math_string.split('\n')
for line in lines[:15]:
    print(line)
if len(lines) > 15:
    print("... (truncated)")

print("\n" + "=" * 70)
print("PROBLEM STATISTICS")
print("=" * 70)
print(f"Number of variables (qubits needed): {qp.get_num_vars()}")

# Get the actual dictionaries of terms to count them
num_linear = len(qp.objective.linear.to_dict())
num_quadratic = len(qp.objective.quadratic.to_dict())

print(f"Number of linear terms (relevance): {num_linear}")
print(f"Number of quadratic terms (redundancy): {num_quadratic}")

print("""
If this ran successfully, it means we have successfully translated a 
Natural Language Processing problem (text retrieval) into a 
Quantum Physics problem (finding the lowest energy state of this equation).
""")

