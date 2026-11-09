"""Token-safe chunks, content-addressed embeddings, and a checked exact FAISS index.

Optional model/search packages are imported only when their capability is used.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from threading import RLock
from time import perf_counter

import numpy as np

from qrag.data import Document, QueryInput
from qrag.experiments.artifacts import file_hash, value_hash, write_json

CHUNK_POLICY = 'sentence-greedy-v1-title64-long-sentence-offset-window-overlap32'


@dataclass(frozen=True)
class Chunk:
    id: str
    source_id: str
    title: str
    text: str
    start: int
    end: int
    sentence_ids: tuple[int, ...]
    embedding_text: str

    @property
    def content_hash(self):
        return hashlib.sha256(self.embedding_text.encode()).hexdigest()


def chunk_document(doc: Document, tokenizer, max_tokens=240, overlap=32) -> tuple[Chunk, ...]:
    """Preserve source character offsets, splitting a long sentence only when needed."""
    if max_tokens < 16 or not 0 <= overlap < max_tokens // 2:
        raise ValueError('Invalid chunk size/overlap')
    title_ids = tokenizer(doc.title, add_special_tokens=False)['input_ids']
    title = tokenizer.decode(title_ids[:64], skip_special_tokens=True)
    prefix = title + '\n'
    count = lambda text: len(tokenizer(prefix + text, add_special_tokens=True)['input_ids'])
    if count('') >= max_tokens - 4:
        raise ValueError('Title consumes chunk token budget')
    spans = []
    offset = 0
    if doc.sentences:
        for i, sentence in enumerate(doc.sentences):
            spans.append((offset, offset + len(sentence), i))
            offset += len(sentence) + 1
    else:
        boundaries = [0, *[m.end() for m in re.finditer(r'[.!?](?:\s+|$)|\n+', doc.text)], len(doc.text)]
        spans = [(a, b, i) for i, (a, b) in enumerate(zip(boundaries, boundaries[1:])) if doc.text[a:b].strip()]
    atoms = []
    for start, end, sid in spans:
        if not doc.text[start:end].strip():
            continue
        if count(doc.text[start:end]) <= max_tokens:
            atoms.append((start, end, sid))
            continue
        offsets = tokenizer(doc.text[start:end], add_special_tokens=False,
                            return_offsets_mapping=True)['offset_mapping']
        pos = 0
        while pos < len(offsets):
            stop = min(len(offsets), pos + max_tokens - count('') - 2)
            while stop > pos and count(doc.text[start + offsets[pos][0]:start + offsets[stop-1][1]]) > max_tokens:
                stop -= 1
            if stop == pos:
                raise ValueError('Cannot represent one token within chunk budget')
            atoms.append((start + offsets[pos][0], start + offsets[stop-1][1], sid))
            if stop == len(offsets):
                break
            pos = max(pos + 1, stop - overlap)
    chunks = []
    i = 0
    while i < len(atoms):
        start, end, _ = atoms[i]
        ids = {atoms[i][2]}
        j = i + 1
        while j < len(atoms) and count(doc.text[start:atoms[j][1]]) <= max_tokens:
            end = atoms[j][1]
            ids.add(atoms[j][2])
            j += 1
        text = doc.text[start:end]
        chunks.append(Chunk(f'{doc.id}:c{len(chunks)}', doc.id, doc.title, text,
                            start, end, tuple(sorted(ids)), prefix + text))
        i = j
    if not chunks:
        raise ValueError('Document has no encodable content')
    return tuple(chunks)


class EmbeddingCache:
    def __init__(self, path: Path, namespace: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.execute('CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, dim INTEGER, digest TEXT, value BLOB)')
        self.namespace = namespace
        self.hits = self.misses = 0
        self.lock = RLock()

    def key(self, text, kind):
        return value_hash({'namespace': self.namespace, 'text': text, 'kind': kind})

    def get(self, text: str, kind='document'):
        with self.lock:
            row = self.connection.execute('SELECT dim,digest,value FROM embeddings WHERE key=?', (self.key(text, kind),)).fetchone()
            if row is None:
                self.misses += 1
                return None
            dim, digest, data = row
            vector = np.frombuffer(data, dtype='<f4').copy()
            if hashlib.sha256(data).hexdigest() != digest or vector.shape != (dim,) or not np.isfinite(vector).all():
                raise ValueError('Corrupt embedding cache entry')
            self.hits += 1
            return vector

    def put(self, text, vector, kind='document'):
        vector = np.asarray(vector, dtype='<f4')
        if vector.ndim != 1 or not len(vector) or not np.isfinite(vector).all():
            raise ValueError('Invalid embedding vector')
        data = vector.tobytes()
        with self.lock, self.connection:
            self.connection.execute('INSERT OR REPLACE INTO embeddings VALUES (?,?,?,?)',
                                    (self.key(text, kind), len(vector), hashlib.sha256(data).hexdigest(), data))

    def close(self):
        self.connection.close()


class ChunkEncoder:
    def __init__(self, embedder, cache_path: Path, model_id: str, revision: str, max_tokens=240):
        self.model = embedder
        self.tokenizer = embedder.tokenizer
        self.max_tokens = min(max_tokens, embedder.max_seq_length)
        self.identity = {'model': model_id, 'revision': revision, 'policy': CHUNK_POLICY,
                         'max_tokens': self.max_tokens, 'normalize': True, 'dtype': 'float32',
                         'document_aggregation': 'mean-chunks-then-unit-normalize'}
        self.cache = EmbeddingCache(cache_path, self.identity)

    def encode(self, texts, kind='document'):
        values = [self.cache.get(t, kind) for t in texts]
        missing = sorted({text for text, value in zip(texts, values) if value is None})
        if missing:
            for text in missing:
                if len(self.tokenizer(text, add_special_tokens=True)['input_ids']) > self.model.max_seq_length:
                    raise ValueError('Unchunked embedding input exceeds model limit')
            vectors = self.model.encode(missing, normalize_embeddings=True, convert_to_numpy=True,
                                        batch_size=64, show_progress_bar=False)
            replacements = dict(zip(missing, vectors, strict=True))
            for text, vector in replacements.items():
                self.cache.put(text, vector, kind)
            values = [replacements[text] if value is None else value for text, value in zip(texts, values)]
        array = np.asarray(values, dtype=np.float32)
        if array.ndim != 2 or not np.isfinite(array).all():
            raise ValueError('Invalid encoded batch')
        return array

    def score(self, query: QueryInput):
        start = perf_counter()
        chunks = [chunk_document(d, self.tokenizer, self.max_tokens) for d in query.documents]
        flattened = [c for group in chunks for c in group]
        vectors = self.encode([c.embedding_text for c in flattened])
        docs, position = [], 0
        for group in chunks:
            vector = vectors[position:position+len(group)].mean(axis=0)
            norm = np.linalg.norm(vector)
            if norm <= 0:
                raise ValueError('Zero document embedding')
            docs.append(vector / norm)
            position += len(group)
        docs = np.asarray(docs, dtype=np.float32)
        question = self.encode([query.question], kind='query')[0]
        return docs @ question, docs @ docs.T, {
            'shared_feature_seconds': perf_counter() - start, 'chunk_count': len(flattened),
            'chunk_ids': [c.id for c in flattened], 'cache_hits_total': self.cache.hits,
            'cache_misses_total': self.cache.misses, 'policy': self.identity,
            'truncated_embedding_positions': [],
        }


def bm25_scores(question: str, documents) -> np.ndarray:
    from rank_bm25 import BM25Okapi
    tokenize = lambda text: re.findall(r'\w+', text.casefold())
    return np.asarray(BM25Okapi([tokenize(d.title + ' ' + d.text) for d in documents]).get_scores(tokenize(question)))


def reciprocal_rank_fusion(*scores, constant=60):
    if not scores or constant <= 0:
        raise ValueError('Need score vectors and positive rank constant')
    n = len(scores[0])
    result = np.zeros(n)
    for vector in scores:
        if np.shape(vector) != (n,) or not np.isfinite(vector).all():
            raise ValueError('Invalid rank vector')
        order = np.argsort(-np.asarray(vector), kind='stable')
        result[order] += 1 / (constant + np.arange(1, n+1))
    return result


class ExactIndex:
    """Immutable FAISS/SQLite bundle, checked against content hashes on load."""
    def __init__(self, directory: Path, expected_identity: dict | None = None):
        import faiss
        metadata = json.loads((directory / 'manifest.json').read_text())
        if expected_identity is not None and metadata['identity'] != expected_identity:
            raise ValueError('Index representation identity mismatch')
        for name, digest in metadata['files'].items():
            if file_hash(directory / name) != digest:
                raise ValueError('Index bundle checksum mismatch')
        self.index = faiss.read_index(str(directory / 'vectors.faiss'))
        with sqlite3.connect(directory / 'metadata.sqlite') as db:
            self.rows = [json.loads(r[0]) for r in db.execute('SELECT payload FROM chunks ORDER BY position')]
        if self.index.ntotal != len(self.rows):
            raise ValueError('Index and metadata length mismatch')
        self.manifest = metadata

    @classmethod
    def build(cls, directory, chunks, vectors, identity):
        import faiss
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        if vectors.ndim != 2 or len(vectors) != len(chunks) or not len(vectors) or not np.isfinite(vectors).all():
            raise ValueError('Invalid index embeddings')
        if len({c.id for c in chunks}) != len(chunks):
            raise ValueError('Duplicate chunk IDs')
        if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-3):
            raise ValueError('Cosine index requires unit embeddings')
        directory.mkdir(parents=True, exist_ok=False)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(directory / 'vectors.faiss'))
        with sqlite3.connect(directory / 'metadata.sqlite') as db:
            db.execute('CREATE TABLE chunks (position INTEGER PRIMARY KEY, payload TEXT)')
            db.executemany('INSERT INTO chunks VALUES (?,?)', [(i, json.dumps(asdict(c))) for i, c in enumerate(chunks)])
        write_json(directory / 'manifest.json', {'identity': identity, 'count': len(chunks),
            'dimension': vectors.shape[1], 'files': {name: file_hash(directory / name) for name in ('vectors.faiss', 'metadata.sqlite')}})
        return cls(directory, identity)

    def search(self, vector, k=10):
        vector = np.asarray(vector, dtype=np.float32)
        if vector.shape != (self.index.d,) or not np.isfinite(vector).all() or k < 1:
            raise ValueError('Invalid search request')
        norm = np.linalg.norm(vector)
        if norm <= 0:
            raise ValueError('Zero query vector')
        scores, positions = self.index.search(np.ascontiguousarray((vector / norm)[None]), min(k, len(self.rows)))
        # Stable secondary ID ordering for exact ties within the retrieved set.
        return sorted([(self.rows[int(i)], float(s)) for i, s in zip(positions[0], scores[0])], key=lambda x: (-x[1], x[0]['id']))


class ChunkReranker:
    def __init__(self, model_name, revision, encoder, device='cpu'):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, revision=revision, device=device, max_length=512)
        self.encoder = encoder
        self.identity = {'model': model_name, 'revision': revision, 'aggregation': 'max-chunk-logit'}

    def score(self, query):
        pairs, groups = [], []
        for i, doc in enumerate(query.documents):
            for chunk in chunk_document(doc, self.encoder.tokenizer, self.encoder.max_tokens):
                # Cross-encoder has its own tokenizer/limit; check paired length.
                if len(self.model.tokenizer(query.question, chunk.embedding_text, truncation=False)['input_ids']) > 512:
                    raise ValueError('Reranker pair exceeds model limit')
                pairs.append((query.question, chunk.embedding_text))
                groups.append(i)
        logits = self.model.predict(pairs, batch_size=32, show_progress_bar=False)
        output = np.full(len(query.documents), -np.inf)
        for group, score in zip(groups, logits, strict=True):
            output[group] = max(output[group], float(score))
        return output
