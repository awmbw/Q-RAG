"""
Script 06: Hyperparameter Tuning
Goal: Find the best alpha and beta to maximize Recall while keeping the 
number of selected documents reasonable.
"""

import json
import sys
import numpy as np

sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever
from src.optimization.qubo_builder import QUBORetriever
from src.optimization.exact_solver import ExactSolver

print("Loading data and models...")
with open("data/processed/dev_set.json", "r") as f:
    dev_data = json.load(f)

# Use 100 questions for tuning so it runs quickly
tuning_data = dev_data[:100]

retriever = DenseRetriever()
exact_solver = ExactSolver()

# We will test these values for beta (Redundancy penalty)
alpha = 1.0
beta_values = [0.0, 0.2, 0.5, 0.8, 1.0]

print("\n" + "=" * 70)
print(f"HYPERPARAMETER SWEEP (Alpha = {alpha})")
print("=" * 70)
print(f"{'Beta':<6} | {'Avg Docs Picked':<16} | {'Recall':<8} | {'Perfect Matches'}")
print("-" * 70)

best_beta = None
best_recall = 0.0

for beta in beta_values:
    qubo_builder = QUBORetriever(alpha=alpha, beta=beta)
    
    total_recall = 0
    total_docs_picked = 0
    perfect_matches = 0
    
    for example in tuning_data:
        # 1. Get raw scores
        result = retriever.retrieve(
            query=example["question"],
            documents=example["documents"]
        )
        
        # 2. Build and solve QUBO
        qp = qubo_builder.build_qubo(
            relevance_scores=result["relevance_scores"],
            pairwise_similarity=result["pairwise_similarity"]
        )
        q_result = exact_solver.solve(qp)
        
        # 3. Extract chosen docs
        selected_docs = qubo_builder.extract_solution(
            q_result["selection_vector"], 
            example["documents"]
        )
        
        # 4. Compute metrics for this question
        num_picked = len(selected_docs)
        relevant_picked = sum(1 for d in selected_docs if d["is_relevant"])
        total_relevant = sum(1 for d in example["documents"] if d["is_relevant"])
        
        recall = relevant_picked / total_relevant if total_relevant > 0 else 0
        
        total_docs_picked += num_picked
        total_recall += recall
        if recall == 1.0:
            perfect_matches += 1

    # Average the metrics over the 100 questions
    avg_recall = total_recall / len(tuning_data)
    avg_docs_picked = total_docs_picked / len(tuning_data)
    
    print(f"{beta:<6.1f} | {avg_docs_picked:<16.1f} | {avg_recall:<8.3f} | {perfect_matches}/100")
    
    if avg_recall > best_recall:
        best_recall = avg_recall
        best_beta = beta

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print("""
- Beta = 0.0: The solver ignores redundancy. It probably picks ALL documents 
  with a positive relevance score (too many docs!).
- High Beta (e.g., 1.0): The solver is terrified of redundancy. It probably 
  picks very few documents, resulting in low recall.
- Our goal is the "Goldilocks Zone": High Recall, but picking around 3-5 docs.
""")
