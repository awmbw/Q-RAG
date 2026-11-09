"""Measure real chunk encoding/cache reuse and round-trip an exact index."""
from dataclasses import replace
import json
from pathlib import Path
from time import perf_counter

from qrag.config import ExperimentConfig
from qrag.data import load_examples
from qrag.models import LocalModels
from qrag.retrieval import ChunkEncoder, ExactIndex, chunk_document
from qrag.experiments.artifacts import write_json


def main():
    from sentence_transformers import SentenceTransformer
    config = replace(ExperimentConfig(), device='cuda', generator_dtype='float16')
    # This profile needs only the embedding model, not generator weights in VRAM.
    model = SentenceTransformer(config.embedding_model, revision=config.embedding_revision,
                                device='cuda', local_files_only=True)
    encoder = ChunkEncoder(model, Path('.cache/retrieval_profile.sqlite'), config.embedding_model, config.embedding_revision)
    queries = load_examples(Path('data/processed/research/hotpotqa_development.json'))[:50]
    passes = []
    for _ in range(2):
        hits, misses, start = encoder.cache.hits, encoder.cache.misses, perf_counter()
        for query, _ in queries:
            encoder.score(query)
        passes.append({'seconds': perf_counter()-start, 'hits': encoder.cache.hits-hits,
                       'misses': encoder.cache.misses-misses})
    chunks = [c for query, _ in queries for doc in query.documents for c in chunk_document(doc, encoder.tokenizer)]
    vectors = encoder.encode([c.embedding_text for c in chunks])
    index_path = Path('.cache/retrieval_profile_index')
    index = ExactIndex(index_path, encoder.identity) if index_path.exists() else ExactIndex.build(index_path, chunks, vectors, encoder.identity)
    vector = encoder.encode([queries[0][0].question], kind='query')[0]
    original = index.search(vector)
    restored = ExactIndex(index_path, encoder.identity).search(vector)
    assert original == restored
    write_json(Path('docs/research_report/evidence/retrieval_profile.json'), {
        'scope': '50 development questions; model already loaded; first pass cache state explicitly recorded',
        'device': 'cuda', 'passes': passes, 'chunks': len(chunks), 'index_roundtrip_identical': True,
        'representation': encoder.identity,
        'first_query_retrieved_ids': [row['id'] for row, score in original]})
    print(passes, len(chunks))
    encoder.cache.close()


if __name__ == '__main__':
    main()
