"""HotpotQA-compatible answer metrics and explicitly document-level evidence metrics.

Reference semantics: https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py
No supporting-sentence prediction is claimed by this first implementation.
"""

from collections import Counter
import re
import string

from qrag.data import Document, EvaluationLabels


def normalize_answer(text: str) -> str:
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())


def answer_metrics(prediction: str, reference: str) -> dict[str, float]:
    pred, gold = normalize_answer(prediction), normalize_answer(reference)
    exact = float(pred == gold)
    specials = {"yes", "no", "noanswer"}
    precision = recall = f1 = 0.0
    if not ((pred in specials or gold in specials) and pred != gold):
        pred_tokens, gold_tokens = pred.split(), gold.split()
        overlap = sum((Counter(pred_tokens) & Counter(gold_tokens)).values())
        if overlap:
            precision = overlap / len(pred_tokens)
            recall = overlap / len(gold_tokens)
            f1 = 2 * precision * recall / (precision + recall)
    return {
        "answer_em": exact,
        "answer_f1": f1,
        "answer_precision": precision,
        "answer_recall": recall,
    }


def evidence_metrics(
    selected: tuple[Document, ...], labels: EvaluationLabels
) -> dict[str, float | None]:
    predicted = {doc.title for doc in selected}
    gold = labels.supporting_titles
    if not gold:
        return {"document_precision": None, "document_recall": None,
                "all_supporting_documents": None}
    correct = len(predicted & gold)
    return {
        "document_precision": correct / len(predicted) if predicted else 0.0,
        "document_recall": correct / len(gold),
        "all_supporting_documents": float(gold <= predicted),
    }
