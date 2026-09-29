"""
Script 03: Test the Dense Retriever on our dataset.
Goal: Verify that embedding-based retrieval correctly ranks relevant documents.
"""

import json
import sys
import numpy as np

# Add the project root to Python's search path so we can import from src/
# Without this, Python wouldn't know where to find src.retrieval
sys.path.insert(0, ".")

from src.retrieval.dense_retriever import DenseRetriever


# ─────────────────────────────────────────────
# STEP 1: Load our processed data
# ─────────────────────────────────────────────
print("Loading processed data...")
with open("data/processed/dev_set.json", "r") as f:
    dev_data = json.load(f)

print(f"Loaded {len(dev_data)} examples")


# ─────────────────────────────────────────────
# STEP 2: Initialize the retriever
# ─────────────────────────────────────────────
retriever = DenseRetriever(model_name="all-MiniLM-L6-v2")
# The model will be loaded automatically on first use (lazy loading)


# ─────────────────────────────────────────────
# STEP 3: Run retrieval on a single example (detailed view)
# ─────────────────────────────────────────────
example = dev_data[0]

print("\n" + "=" * 70)
print("DETAILED RETRIEVAL: Example 0")
print("=" * 70)
print(f"\nQuestion: {example['question']}")
print(f"Answer: {example['answer']}")
print(f"Type: {example['type']}")

# Run the full retrieval pipeline
result = retriever.retrieve(
    query=example["question"],
    documents=example["documents"]
)

# Display results: relevance scores ranked from highest to lowest
print(f"\n{'Rank':<6} {'Score':<8} {'Relevant?':<10} {'Title'}")
print("-" * 70)

for rank, idx in enumerate(result["ranked_indices"]):
    doc = example["documents"][idx]
    score = result["relevance_scores"][idx]
    status = "✅ YES" if doc["is_relevant"] else "❌ no"
    print(f"  {rank+1:<4} {score:<8.4f} {status:<10} {doc['title']}")


# ─────────────────────────────────────────────
# STEP 4: Visualize the pairwise similarity matrix
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("PAIRWISE SIMILARITY MATRIX (Redundancy)")
print("=" * 70)

sim_matrix = result["pairwise_similarity"]
titles_short = [d["title"][:20] for d in example["documents"]]

# Print header
print(f"\n{'':>22}", end="")
for i in range(len(titles_short)):
    print(f"  D{i:<3}", end="")
print()

# Print matrix rows
for i in range(len(titles_short)):
    label = f"D{i} {titles_short[i]}"
    print(f"  {label:>20}", end="")
    for j in range(len(titles_short)):
        val = sim_matrix[i][j]
        print(f" {val:5.2f}", end="")
    print()


# ─────────────────────────────────────────────
# STEP 5: Evaluate retrieval across multiple examples
# ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("BATCH EVALUATION: First 50 examples")
print("=" * 70)

# For each question, check: do the relevant docs appear in the top-k?
def recall_at_k(ranked_indices, documents, k):
    """
    What fraction of relevant documents appear in the top-k results?
    
    Example: 2 relevant docs, top-3 contains 1 of them → recall = 0.5
    """
    top_k_indices = ranked_indices[:k]
    relevant_in_top_k = sum(
        1 for idx in top_k_indices if documents[idx]["is_relevant"]
    )
    total_relevant = sum(1 for d in documents if d["is_relevant"])
    
    if total_relevant == 0:
        return 0.0
    return relevant_in_top_k / total_relevant


results_summary = {
    "recall@2": [],
    "recall@3": [],
    "recall@4": [],
    "recall@5": [],
    "relevant_rank_avg": [],   # average rank of relevant documents
}

for i, example in enumerate(dev_data[:50]):
    result = retriever.retrieve(
        query=example["question"],
        documents=example["documents"]
    )
    
    # Compute recall at different k values
    for k in [2, 3, 4, 5]:
        r = recall_at_k(
            result["ranked_indices"],
            example["documents"],
            k
        )
        results_summary[f"recall@{k}"].append(r)
    
    # Find where the relevant documents are ranked
    for idx in result["ranked_indices"]:
        if example["documents"][idx]["is_relevant"]:
            rank_position = list(result["ranked_indices"]).index(idx) + 1
            results_summary["relevant_rank_avg"].append(rank_position)
    
    # Progress indicator
    if (i + 1) % 10 == 0:
        print(f"  Processed {i + 1}/50 examples...")


# Print summary statistics
print(f"\n{'Metric':<25} {'Mean':<10} {'Interpretation'}")
print("-" * 70)

for k in [2, 3, 4, 5]:
    mean_recall = np.mean(results_summary[f"recall@{k}"])
    print(f"  Recall@{k:<18} {mean_recall:<10.3f} "
          f"{'(% of relevant docs found in top-' + str(k) + ')'}")

avg_rank = np.mean(results_summary["relevant_rank_avg"])
print(f"  Avg rank of relevant   {avg_rank:<10.2f} "
      f"(lower is better, 1.0 = perfect)")

print("\n" + "=" * 70)
print("WHAT THESE NUMBERS MEAN")
print("=" * 70)
print("""
- Recall@3 ≈ 0.8+ means the retriever finds most relevant docs in top 3
- Recall@5 ≈ 0.9+ means almost all relevant docs appear in top 5
- These are the BASELINE numbers that our quantum optimizer will try to BEAT
  by also considering redundancy (not just raw relevance)

If Recall@3 is low, the embedding model might not be good enough,
and we'd need to try a different one (e.g., bge-small-en-v1.5).
""")
