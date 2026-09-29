"""
Script 02: Create a working subset of HotpotQA.
Save it locally so we don't re-download every time.
"""

from datasets import load_dataset
import json
import os
import random

# ─────────────────────────────────────────────
# STEP 1: Load the full dataset (uses cache from previous run)
# ─────────────────────────────────────────────
print("Loading HotpotQA from cache...")
dataset = load_dataset("hotpotqa/hotpot_qa", "distractor")

# ─────────────────────────────────────────────
# STEP 2: Create our subsets
# ─────────────────────────────────────────────
# We set a random seed so our selection is REPRODUCIBLE.
# Without this, every run would pick different questions,
# making it impossible to compare experiments fairly.
random.seed(42)   # 42 is a convention (Hitchhiker's Guide reference)

# Get indices and shuffle them
train_indices = list(range(len(dataset["train"])))
random.shuffle(train_indices)

val_indices = list(range(len(dataset["validation"])))
random.shuffle(val_indices)

# Select our subsets
dev_indices = train_indices[:1000]     # 1000 for development
eval_indices = val_indices[:500]       # 500 for evaluation

print(f"Development set: {len(dev_indices)} questions")
print(f"Evaluation set: {len(eval_indices)} questions")

# ─────────────────────────────────────────────
# STEP 3: Extract and flatten each example
# ─────────────────────────────────────────────
# We'll convert each example into a cleaner format
# that's easier to work with in our pipeline.

def process_example(example):
    """
    Convert a raw HotpotQA example into our project's format.
    
    Takes the nested HuggingFace format and produces a flat,
    easy-to-use dictionary with pre-joined document texts.
    """
    # Join sentences into full document text for each candidate
    documents = []
    for title, sents in zip(
        example["context"]["title"],
        example["context"]["sentences"]
    ):
        documents.append({
            "title": title,
            "text": " ".join(sents),    # combine sentences into one string
            "sentences": sents,          # keep original sentences too
            "num_sentences": len(sents)
        })
    
    # Figure out which documents are relevant (ground truth)
    relevant_titles = set(example["supporting_facts"]["title"])
    for doc in documents:
        doc["is_relevant"] = doc["title"] in relevant_titles
    
    return {
        "id": example["id"],
        "question": example["question"],
        "answer": example["answer"],
        "type": example["type"],
        "level": example["level"],
        "documents": documents,
        "supporting_facts": {
            "titles": list(relevant_titles),
            "details": [
                {"title": t, "sent_id": s}
                for t, s in zip(
                    example["supporting_facts"]["title"],
                    example["supporting_facts"]["sent_id"]
                )
            ]
        },
        "num_candidates": len(documents),
        "num_relevant": sum(1 for d in documents if d["is_relevant"])
    }


# Process all examples in our subsets
print("\nProcessing development set...")
dev_data = [process_example(dataset["train"][i]) for i in dev_indices]

print("Processing evaluation set...")
eval_data = [process_example(dataset["validation"][i]) for i in eval_indices]

# ─────────────────────────────────────────────
# STEP 4: Save to disk
# ─────────────────────────────────────────────
os.makedirs("data/processed", exist_ok=True)

with open("data/processed/dev_set.json", "w") as f:
    json.dump(dev_data, f, indent=2)

with open("data/processed/eval_set.json", "w") as f:
    json.dump(eval_data, f, indent=2)

dev_size_mb = os.path.getsize("data/processed/dev_set.json") / (1024 * 1024)
eval_size_mb = os.path.getsize("data/processed/eval_set.json") / (1024 * 1024)

print(f"\nSaved: data/processed/dev_set.json ({dev_size_mb:.1f} MB)")
print(f"Saved: data/processed/eval_set.json ({eval_size_mb:.1f} MB)")

# ─────────────────────────────────────────────
# STEP 5: Quick sanity check
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("SANITY CHECK")
print("=" * 60)

sample = dev_data[0]
print(f"\nQuestion: {sample['question']}")
print(f"Answer: {sample['answer']}")
print(f"Type: {sample['type']}, Level: {sample['level']}")
print(f"Candidates: {sample['num_candidates']}, Relevant: {sample['num_relevant']}")
print(f"\nDocuments:")
for i, doc in enumerate(sample["documents"]):
    status = "✅" if doc["is_relevant"] else "❌"
    print(f"  {status} [{doc['title']}] ({len(doc['text'])} chars)")

print("\n✅ Subset preparation complete!")
print("From now on, we load from data/processed/ — no more downloading.")
