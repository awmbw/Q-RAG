"""Bounded corpus retrieval built from inference documents, without annotations."""

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np

from qrag.data import Document
from qrag.experiments.artifacts import file_hash, value_hash, write_json
from qrag.retrieval import ExactIndex, chunk_document, reciprocal_rank_fusion


def corpus_id(title, text):
    return "corpus:" + hashlib.sha256((title + "\n" + text).encode()).hexdigest()[:24]


def deduplicate(documents):
    unique = {}
    for doc in documents:
        key = corpus_id(doc.title, doc.text)
        unique.setdefault(key, Document(key, doc.title, doc.text, doc.sentences, key))
    return tuple(unique[key] for key in sorted(unique))


class CorpusRetriever:
    def __init__(self, directory: Path, encoder):
        from rank_bm25 import BM25Okapi

        manifest = json.loads((directory / "corpus.json").read_text())
        if (
            manifest["representation"] != encoder.identity
            or file_hash(directory / "documents.json") != manifest["documents_sha256"]
        ):
            raise ValueError("Corpus metadata/representation mismatch")
        self.documents = tuple(
            Document(**{**d, "sentences": tuple(d["sentences"])})
            for d in json.loads((directory / "documents.json").read_text())
        )
        self.index = ExactIndex(directory / "index", encoder.identity)
        self.encoder = encoder
        self.positions = {d.id: i for i, d in enumerate(self.documents)}
        self.bm25 = BM25Okapi(
            [
                re.findall(r"\w+", (d.title + " " + d.text).casefold())
                for d in self.documents
            ]
        )
        self.manifest = manifest

    @classmethod
    def build(cls, directory, documents, encoder):
        docs = deduplicate(documents)
        content_identity = value_hash([(d.id, d.title, d.text) for d in docs])
        if directory.exists():
            manifest = json.loads((directory / "corpus.json").read_text())
            if manifest["content_identity"] != content_identity:
                raise ValueError("Existing corpus has different source content")
            return cls(directory, encoder)
        directory.mkdir(parents=True)
        chunks = [
            c
            for d in docs
            for c in chunk_document(d, encoder.tokenizer, encoder.max_tokens)
        ]
        vectors = encoder.encode([c.embedding_text for c in chunks])
        ExactIndex.build(directory / "index", chunks, vectors, encoder.identity)
        write_json(directory / "documents.json", [asdict(d) for d in docs])
        write_json(
            directory / "corpus.json",
            {
                "content_identity": content_identity,
                "documents": len(docs),
                "chunks": len(chunks),
                "representation": encoder.identity,
                "documents_sha256": file_hash(directory / "documents.json"),
                "scope": "bounded union of benchmark input passages; not full Wikipedia",
            },
        )
        return cls(directory, encoder)

    def retrieve(self, question, count=100, mode="hybrid", unique_titles=False):
        started = perf_counter()
        if mode not in {"dense", "bm25", "hybrid"} or count < 1:
            raise ValueError("Invalid corpus retrieval settings")
        vector = self.encoder.encode([question], kind="query")[0]
        hits = self.index.search(vector, len(self.index.rows))
        dense = np.full(len(self.documents), -1.0, dtype=float)
        for chunk, score in hits:
            position = self.positions[chunk["source_id"]]
            dense[position] = max(dense[position], score)
        lexical = np.asarray(
            self.bm25.get_scores(re.findall(r"\w+", question.casefold()))
        )
        scores = {
            "dense": dense,
            "bm25": lexical,
            "hybrid": reciprocal_rank_fusion(dense, lexical),
        }[mode]
        selected = []
        seen = set()
        for position in np.argsort(-scores, kind="stable"):
            doc = self.documents[int(position)]
            if unique_titles and doc.title in seen:
                continue
            seen.add(doc.title)
            selected.append(doc)
            if len(selected) == count:
                break
        return tuple(selected), {
            "seconds": perf_counter() - started,
            "mode": mode,
            "requested": count,
            "returned": len(selected),
            "corpus_documents": len(self.documents),
            "candidate_ids": [d.id for d in selected],
        }
