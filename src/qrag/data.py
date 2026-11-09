"""Adapt the existing processed HotpotQA data without passing labels to selectors."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str


@dataclass(frozen=True)
class QueryInput:
    id: str
    question: str
    documents: tuple[Document, ...]


@dataclass(frozen=True)
class EvaluationLabels:
    answer: str
    supporting_titles: frozenset[str]


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def adapt_example(raw: dict) -> tuple[QueryInput, EvaluationLabels]:
    """The first object is safe for inference; only the evaluator gets the second."""
    query_id = _string(raw["id"], "id")
    question = _string(raw["question"], "question")
    raw_documents = raw["documents"]
    if not isinstance(raw_documents, list) or not raw_documents:
        raise ValueError(f"{query_id}: documents must be a nonempty list")
    documents = tuple(
        Document(
            id=f"{query_id}:d{i}",
            title=_string(doc["title"], "title"),
            text=_string(doc["text"], "text"),
        )
        for i, doc in enumerate(raw_documents)
    )
    if len({doc.title for doc in documents}) != len(documents):
        raise ValueError(f"{query_id}: duplicate document titles are ambiguous")
    # Gold annotations are read only into the evaluation object.
    support = raw.get("supporting_facts", {}).get("titles")
    if support is None:
        support = [doc["title"] for doc in raw_documents if doc.get("is_relevant")]
    if not isinstance(support, list) or any(not isinstance(t, str) for t in support):
        raise ValueError(f"{query_id}: invalid supporting titles")
    labels = EvaluationLabels(_string(raw["answer"], "answer"), frozenset(support))
    return QueryInput(query_id, question, documents), labels


def load_examples(path: Path) -> list[tuple[QueryInput, EvaluationLabels]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Dataset must be a nonempty JSON list")
    examples = [adapt_example(example) for example in raw]
    if len({query.id for query, _ in examples}) != len(examples):
        raise ValueError("Dataset contains duplicate question IDs")
    return examples
