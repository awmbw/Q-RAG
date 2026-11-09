"""Adapt the existing processed HotpotQA data without passing labels to selectors."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    sentences: tuple[str, ...] = ()
    source_id: str = ""


@dataclass(frozen=True)
class QueryInput:
    id: str
    question: str
    documents: tuple[Document, ...]


@dataclass(frozen=True)
class EvaluationLabels:
    answer: str
    supporting_titles: frozenset[str]
    supporting_sentences: frozenset[tuple[str, int]] = frozenset()
    aliases: tuple[str, ...] = ()
    dataset: str = "hotpotqa"
    supporting_ids: frozenset[str] = frozenset()


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
            sentences=tuple(doc.get("sentences", ())),
            source_id=str(doc.get("source_id", f"{query_id}:d{i}")),
        )
        for i, doc in enumerate(raw_documents)
    )
    if raw.get("dataset", "hotpotqa") != "musique" and len({doc.title for doc in documents}) != len(documents):
        raise ValueError(f"{query_id}: duplicate document titles are ambiguous")
    # Gold annotations are read only into the evaluation object.
    support = raw.get("supporting_facts", {}).get("titles")
    if support is None:
        support = [doc["title"] for doc in raw_documents if doc.get("is_relevant")]
    if not isinstance(support, list) or any(not isinstance(t, str) for t in support):
        raise ValueError(f"{query_id}: invalid supporting titles")
    for doc in documents:
        if any(not isinstance(s, str) for s in doc.sentences):
            raise ValueError(f"{query_id}: sentences must be strings")
        if doc.sentences and " ".join(doc.sentences) != doc.text:
            raise ValueError(f"{query_id}: sentence join differs from source text")
    details = raw.get("supporting_facts", {}).get("details", [])
    sentence_labels = frozenset((d["title"], int(d["sent_id"])) for d in details)
    by_title = {doc.title: doc for doc in documents}
    for title, index in sentence_labels:
        if title not in by_title or not 0 <= index < len(by_title[title].sentences):
            raise ValueError(f"{query_id}: invalid supporting sentence mapping")
    if not set(support) <= set(by_title):
        raise ValueError(f"{query_id}: supporting title missing from candidates")
    aliases = raw.get("answer_aliases", [])
    if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
        raise ValueError(f"{query_id}: invalid answer aliases")
    supporting_ids = frozenset(raw.get("supporting_ids", []))
    if not supporting_ids <= {doc.id for doc in documents}:
        raise ValueError(f"{query_id}: supporting ID missing from candidates")
    labels = EvaluationLabels(_string(raw["answer"], "answer"), frozenset(support),
                              sentence_labels, tuple(aliases), raw.get("dataset", "hotpotqa"),
                              supporting_ids)
    return QueryInput(query_id, question, documents), labels


def load_examples(path: Path) -> list[tuple[QueryInput, EvaluationLabels]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Dataset must be a nonempty JSON list")
    examples = [adapt_example(example) for example in raw]
    if len({query.id for query, _ in examples}) != len(examples):
        raise ValueError("Dataset contains duplicate question IDs")
    return examples
