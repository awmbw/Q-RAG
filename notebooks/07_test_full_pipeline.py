"""
Script 07: Test Full Pipeline End-to-End
Goal: Retrieve, Quantum Optimize, and Generate an answer using the LLM.
"""

import json
import sys
import time

sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever
from src.optimization.qubo_builder import QUBORetriever
from src.optimization.exact_solver import ExactSolver
from src.generation.llm_generator import LLMGenerator

print("Loading Data...")
with open("data/processed/dev_set.json", "r") as f:
    dev_data = json.load(f)

# Pick an interesting multi-hop question!
example = dev_data[0]

# ─────────────────────────────────────────────
# 1. INITIALIZE ALL MODULES
# ─────────────────────────────────────────────
print("\nInitializing Pipeline Modules...")
retriever = DenseRetriever()
qubo_builder = QUBORetriever(alpha=1.0, beta=0.2)  # The Goldilocks parameters!
exact_solver = ExactSolver()
generator = LLMGenerator()

# Load models into memory
retriever.load_model()
generator.load_model()

# ─────────────────────────────────────────────
# 2. RUN PIPELINE
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"QUESTION: {example['question']}")
print("=" * 70)

start_time = time.time()

# Step A: Dense Retrieval
print("1. Dense Retrieval (Embedding calculation)...")
retrieval_result = retriever.retrieve(
    query=example["question"],
    documents=example["documents"]
)

# Step B: Quantum Optimization
print("2. Quantum Optimization (Redundancy pruning)...")
qp = qubo_builder.build_qubo(
    relevance_scores=retrieval_result["relevance_scores"],
    pairwise_similarity=retrieval_result["pairwise_similarity"]
)
q_result = exact_solver.solve(qp)
selected_docs = qubo_builder.extract_solution(
    q_result["selection_vector"], 
    example["documents"]
)
print(f"   -> Selected {len(selected_docs)} out of {len(example['documents'])} candidate documents.")

# Step C: LLM Generation
print("3. LLM Generation...")
final_answer = generator.generate(
    question=example["question"],
    selected_docs=selected_docs
)

end_time = time.time()

# ─────────────────────────────────────────────
# 3. RESULTS
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("FINAL PIPELINE OUTPUT")
print("=" * 70)

print(f"Q: {example['question']}")
print(f"\nAI ANSWER: {final_answer}")
print(f"\nGround Truth Answer: {example['answer']}")
print("-" * 70)
print(f"Total pipeline execution time: {end_time - start_time:.2f} seconds")

print("\nDocuments passed to the LLM as context:")
for doc in selected_docs:
    status = "✅" if doc["is_relevant"] else "❌"
    print(f"  {status} {doc['title']}")
