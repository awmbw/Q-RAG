"""
Script 05: Test the QAOA Solver.
Goal: Run the quantum optimizer on our QUBO and see which documents it selects!
"""

import json
import sys
import numpy as np

sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever
from src.optimization.qubo_builder import QUBORetriever
from src.optimization.exact_solver import ExactSolver

# ─────────────────────────────────────────────
# STEP 1: Load Data & Initialize Modules
# ─────────────────────────────────────────────
print("Loading data and initializing models...")
with open("data/processed/dev_set.json", "r") as f:
    dev_data = json.load(f)

# The full Q-RAG stack!
retriever = DenseRetriever()
qubo_builder = QUBORetriever(alpha=1.0, beta=0.5)
# QAOA with 1 layer (reps=1) and max 50 classical tweaks
exact_solver = ExactSolver()

# ─────────────────────────────────────────────
# STEP 2: Retrieval & QUBO Generation
# ─────────────────────────────────────────────
example = dev_data[0]
print(f"\nQuestion: {example['question']}")
print(f"Ground Truth Answer: {example['answer']}\n")

# Get embedding scores
result = retriever.retrieve(
    query=example["question"],
    documents=example["documents"]
)

# Build the math problem
qp = qubo_builder.build_qubo(
    relevance_scores=result["relevance_scores"],
    pairwise_similarity=result["pairwise_similarity"]
)

# ─────────────────────────────────────────────
# STEP 3: Quantum Optimization
# ─────────────────────────────────────────────
# This will simulate a quantum computer searching for the best binary string
qaoa_result = exact_solver.solve(qp)
print(f"Solved in {qaoa_result['time_taken']:.4f} seconds!")

# Map the binary string back to actual documents
selected_docs = qubo_builder.extract_solution(
    qaoa_result["selection_vector"], 
    example["documents"]
)

# ─────────────────────────────────────────────
# STEP 4: Analyze the Results
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("QAOA SELECTION RESULTS")
print("=" * 70)

print(f"Optimal binary string found: {qaoa_result['selection_vector']}")
print(f"Number of documents selected: {len(selected_docs)} out of {len(example['documents'])}")

print("\nDocuments chosen by the Quantum Optimizer:")
for doc in selected_docs:
    status = "✅ RELEVANT" if doc["is_relevant"] else "❌ distractor"
    # Find its original index to look up its relevance score
    idx = example["documents"].index(doc)
    score = result["relevance_scores"][idx]
    print(f"  {status:<12} (Score: {score:.4f})  {doc['title']}")

print("\n" + "=" * 70)
print("DID IT WORK?")
print("=" * 70)
# Did QAOA successfully select both ground truth documents?
relevant_selected = sum(1 for d in selected_docs if d["is_relevant"])
total_relevant = sum(1 for d in example["documents"] if d["is_relevant"])

if relevant_selected == total_relevant:
    print("🎉 SUCCESS! QAOA found all the relevant documents!")
else:
    print(f"⚠️ QAOA found {relevant_selected} out of {total_relevant} relevant docs.")
    print("This means we need to tune alpha and beta, or increase QAOA reps!")
