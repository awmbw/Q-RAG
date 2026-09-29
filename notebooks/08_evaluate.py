"""
Script 08: Academic Evaluation
Goal: Mathematically prove that Q-RAG outperforms standard Top-K RAG
on the 500-question evaluation set.
"""

import json
import sys
import numpy as np

sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever
from src.optimization.qubo_builder import QUBORetriever
from src.optimization.exact_solver import ExactSolver

print("Loading data and models...")
with open("data/processed/eval_set.json", "r") as f:
    eval_data = json.load(f)

retriever = DenseRetriever()
qubo_builder = QUBORetriever(alpha=1.0, beta=0.2)
exact_solver = ExactSolver()

# Tracking metrics
metrics = {
    "standard_rag": {"recall": [], "precision": [], "f1": [], "num_docs": []},
    "q_rag": {"recall": [], "precision": [], "f1": [], "num_docs": []}
}

def calculate_metrics(selected_docs, total_relevant_count):
    if len(selected_docs) == 0:
        return 0.0, 0.0, 0.0
        
    relevant_picked = sum(1 for d in selected_docs if d["is_relevant"])
    
    # Recall: What % of the truly relevant docs did we find?
    recall = relevant_picked / total_relevant_count if total_relevant_count > 0 else 0.0
    
    # Precision: What % of the docs we picked were actually relevant?
    precision = relevant_picked / len(selected_docs)
    
    # F1 Score: The harmonic mean of Precision and Recall
    f1 = 0.0
    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
        
    return recall, precision, f1

print(f"\nEvaluating {len(eval_data)} questions. This will take ~10 seconds...")

for i, example in enumerate(eval_data):
    total_relevant = sum(1 for d in example["documents"] if d["is_relevant"])
    if total_relevant == 0:
        continue

    # 1. Base Retrieval
    result = retriever.retrieve(
        query=example["question"],
        documents=example["documents"]
    )
    
    # ==========================================
    # METHOD 1: Standard RAG (Top-5)
    # ==========================================
    # Get indices of top 5 scores
    top_5_indices = np.argsort(result["relevance_scores"])[-5:][::-1]
    standard_docs = [example["documents"][idx] for idx in top_5_indices]
    
    r_std, p_std, f1_std = calculate_metrics(standard_docs, total_relevant)
    metrics["standard_rag"]["recall"].append(r_std)
    metrics["standard_rag"]["precision"].append(p_std)
    metrics["standard_rag"]["f1"].append(f1_std)
    metrics["standard_rag"]["num_docs"].append(len(standard_docs))
    
    # ==========================================
    # METHOD 2: Q-RAG (QUBO Optimization)
    # ==========================================
    qp = qubo_builder.build_qubo(
        relevance_scores=result["relevance_scores"],
        pairwise_similarity=result["pairwise_similarity"]
    )
    q_result = exact_solver.solve(qp)
    qrag_docs = qubo_builder.extract_solution(q_result["selection_vector"], example["documents"])
    
    r_q, p_q, f1_q = calculate_metrics(qrag_docs, total_relevant)
    metrics["q_rag"]["recall"].append(r_q)
    metrics["q_rag"]["precision"].append(p_q)
    metrics["q_rag"]["f1"].append(f1_q)
    metrics["q_rag"]["num_docs"].append(len(qrag_docs))

# ==========================================
# FINAL REPORT
# ==========================================
print("\n" + "=" * 50)
print("FINAL EVALUATION RESULTS (500 Questions)")
print("=" * 50)

def print_stats(name, data):
    print(f"\n{name.upper()}:")
    print(f"  Avg Docs Picked : {np.mean(data['num_docs']):.2f}")
    print(f"  Avg Recall      : {np.mean(data['recall']):.3f}")
    print(f"  Avg Precision   : {np.mean(data['precision']):.3f}")
    print(f"  Avg F1 Score    : {np.mean(data['f1']):.3f}")

print_stats("Standard RAG (Top-5 Baseline)", metrics["standard_rag"])
print_stats("Q-RAG (Quantum Optimization)", metrics["q_rag"])
