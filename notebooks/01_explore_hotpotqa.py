"""
Script 01: Download and explore the HotpotQA dataset.
Goal: Understand the data structure before building the retrieval pipeline.
"""

from datasets import load_dataset
import json

# ─────────────────────────────────────────────
# STEP 1: Download HotpotQA
# ─────────────────────────────────────────────
# HotpotQA has two configs:
#   - "fullwiki": questions + the entire Wikipedia (huge, ~GB)
#   - "distractor": questions + 10 candidate paragraphs per question (manageable)
#
# We use "distractor" because:
#   - It already gives us a small candidate pool (~10 docs per query)
#   - This aligns perfectly with our problem: n ∈ [6, 12] candidates
#   - No need to build our own retrieval index from scratch
#
print("Downloading HotpotQA (distractor setting)...")
dataset = load_dataset("hotpotqa/hotpot_qa", "distractor")

# Let's see what splits are available
print(f"\nAvailable splits: {list(dataset.keys())}")
print(f"Training set size: {len(dataset['train'])}")
print(f"Validation set size: {len(dataset['validation'])}")


# ─────────────────────────────────────────────
# STEP 2: Examine a single example
# ─────────────────────────────────────────────
# Let's look at ONE question in detail to understand the structure.
example = dataset["train"][0]

print("\n" + "=" * 60)
print("STRUCTURE OF ONE EXAMPLE")
print("=" * 60)
print(f"\nFields available: {list(example.keys())}")

# Print each field with its type and a preview
for key, value in example.items():
    if isinstance(value, list):
        print(f"\n  {key} (list, length={len(value)}):")
        # Show first 2 items
        for i, item in enumerate(value[:2]):
            preview = str(item)[:100]
            print(f"    [{i}]: {preview}...")
    else:
        preview = str(value)[:200]
        print(f"\n  {key} ({type(value).__name__}): {preview}")


# ─────────────────────────────────────────────
# STEP 3: Deep dive into the context structure
# ─────────────────────────────────────────────
# The "context" field is the most important for us.
# It contains the candidate documents we'll be selecting from.

print("\n" + "=" * 60)
print("DEEP DIVE: CONTEXT (CANDIDATE DOCUMENTS)")
print("=" * 60)

titles = example["context"]["title"]
sentences = example["context"]["sentences"]

print(f"\nQuestion: {example['question']}")
print(f"Answer: {example['answer']}")
print(f"Number of candidate documents: {len(titles)}")

for i, (title, sents) in enumerate(zip(titles, sentences)):
    full_text = " ".join(sents)
    print(f"\n  Doc {i}: [{title}]")
    print(f"    Sentences: {len(sents)}")
    print(f"    Preview: {full_text[:150]}...")


# ─────────────────────────────────────────────
# STEP 4: Understand supporting facts
# ─────────────────────────────────────────────
# "supporting_facts" tells us WHICH documents (and sentences)
# actually contain the answer. This is our GROUND TRUTH for evaluation.
# If our optimizer selects these documents → good retrieval.

print("\n" + "=" * 60)
print("SUPPORTING FACTS (GROUND TRUTH)")
print("=" * 60)

sup_titles = example["supporting_facts"]["title"]
sup_sent_ids = example["supporting_facts"]["sent_id"]

print(f"\nSupporting document titles: {set(sup_titles)}")
print(f"\nDetailed supporting facts:")
for title, sent_id in zip(sup_titles, sup_sent_ids):
    print(f"  - Document: [{title}], Sentence index: {sent_id}")

# Show which documents are relevant vs irrelevant (distractors)
relevant_titles = set(sup_titles)
print(f"\nOf {len(titles)} candidate docs:")
print(f"  ✅ Relevant: {len(relevant_titles)}")
print(f"  ❌ Distractors: {len(titles) - len(relevant_titles)}")


# ─────────────────────────────────────────────
# STEP 5: Check question types and difficulty
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("QUESTION TYPES & DIFFICULTY")
print("=" * 60)

# HotpotQA labels each question with a type and difficulty level
print(f"  Type: {example['type']}")
print(f"  Level: {example['level']}")

# Let's see the distribution across the training set
from collections import Counter
types = Counter(ex["type"] for ex in dataset["train"])
levels = Counter(ex["level"] for ex in dataset["train"])

print(f"\nQuestion type distribution: {dict(types)}")
print(f"Difficulty distribution: {dict(levels)}")


print("\n" + "=" * 60)
print("✅ EXPLORATION COMPLETE")
print("=" * 60)
print("""
Key takeaways for our project:
1. Each question comes with ~10 candidate documents (perfect for n ∈ [6,12])
2. Only 2 documents are typically relevant (multi-hop)
3. The rest are distractors — our optimizer must learn to avoid them
4. 'supporting_facts' gives us ground truth for evaluation
""")
