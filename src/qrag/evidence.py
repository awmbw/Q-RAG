"""Transparent entity-link features, not verified semantic relation extraction."""
from dataclasses import dataclass
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from time import perf_counter
import numpy as np

from qrag.experiments.artifacts import value_hash

STOP = {'the','a','an','of','in','on','at','for','and','or','is','was','were','what','who','which',
        'to','from','by','with','did','does','do','this','that','it','as','are','has','had','be','when','where'}
EXTRACTOR_REVISION = 'entity-link-regex-title-v1'


def terms(text):
    return set(re.findall(r'\w+', text.casefold())) - STOP


def mentions(doc, title_aliases):
    found = []
    for entity in sorted(title_aliases):
        for match in re.finditer(r'(?<!\w)' + re.escape(entity) + r'(?!\w)', doc.text, re.IGNORECASE):
            found.append({'entity': entity, 'start': match.start(), 'end': match.end(), 'kind': 'candidate-title'})
    for match in re.finditer(r'\b[A-Z][\w\'-]*(?:\s+(?:[A-Z][\w\'-]*|of|the|and)){0,4}', doc.text):
        entity = match.group().casefold().strip()
        if len(terms(entity)) and len(entity) >= 3:
            found.append({'entity': entity, 'start': match.start(), 'end': match.end(), 'kind': 'capitalized-span'})
    return sorted(found, key=lambda x: (x['start'], x['end'], x['entity']))


def build_evidence(query, relevance):
    start = perf_counter()
    aliases = {re.sub(r'\s*\([^)]*\)', '', d.title).strip().casefold() for d in query.documents}
    aliases = {a for a in aliases if len(a) >= 3 and terms(a)}
    extracted = [mentions(doc, aliases) for doc in query.documents]
    entities = [{m['entity'] for m in group} | {doc.title.casefold()} for doc, group in zip(query.documents, extracted)]
    question_terms = sorted(terms(query.question))
    coverage = np.array([[float(term in terms(d.title + ' ' + d.text)) for term in question_terms]
                         for d in query.documents])
    if not question_terms:
        coverage = np.zeros((len(query.documents), 1))
    anchors = coverage.mean(axis=1)
    comp = np.zeros((len(query.documents), len(query.documents)))
    edges = []
    for i in range(len(query.documents)):
        for j in range(i+1, len(query.documents)):
            shared = entities[i] & entities[j]
            if shared:
                weight = max(anchors[i], anchors[j]) * np.sqrt(max(0, relevance[i]) * max(0, relevance[j]))
                comp[i, j] = comp[j, i] = weight
                edges.append({'source': query.documents[i].id, 'target': query.documents[j].id,
                              'entities': sorted(shared), 'weight': float(weight)})
    graph = {'kind': 'entity-link graph; unverified lexical links, not a factual relation graph',
             'extractor_revision': EXTRACTOR_REVISION,
             'identity': value_hash({'question': query.question, 'documents': [(d.id,d.title,d.text) for d in query.documents],
                                     'relevance': np.asarray(relevance).tolist(), 'extractor': EXTRACTOR_REVISION}),
             'mentions': {d.id: group for d, group in zip(query.documents, extracted)},
             'edges': edges, 'query_terms': question_terms, 'anchors': anchors.tolist(),
             'seconds': perf_counter()-start}
    # Every mention is independently checkable against its exact source span.
    for doc, group in zip(query.documents, extracted):
        for m in group:
            assert doc.text[m['start']:m['end']].casefold() == m['entity']
    return comp, coverage, graph


def interaction_problem(relevance, similarities, k, gamma=0., complementarity=None,
                        alpha=1., beta=.2, **budgets):
    from qrag.optimization import SelectionProblem
    comp = np.zeros_like(similarities) if complementarity is None else np.asarray(complementarity)
    if comp.shape != np.shape(similarities) or not np.isfinite(comp).all() or np.any(comp < 0):
        raise ValueError('Invalid complementarity')
    if not np.isfinite([alpha,beta,gamma]).all() or min(alpha,beta,gamma) < 0:
        raise ValueError('Invalid objective weights')
    return SelectionProblem(-alpha*np.asarray(relevance), np.triu(beta*np.maximum(similarities,0)-gamma*comp,1), k, **budgets)


def cached_evidence(query, relevance, path: Path):
    """Cache only inference-derived features; reject damaged extraction artifacts."""
    started = perf_counter()
    key = value_hash({'query':asdict(query),'relevance':np.asarray(relevance).tolist(),
                      'extractor':EXTRACTOR_REVISION})
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS graphs (key TEXT PRIMARY KEY, digest TEXT, payload TEXT)')
        row=db.execute('SELECT digest,payload FROM graphs WHERE key=?',(key,)).fetchone()
        if row:
            digest,payload=row
            if hashlib.sha256(payload.encode()).hexdigest()!=digest:
                raise ValueError('Corrupt graph cache entry')
            result=json.loads(payload)
            comp,coverage=np.array(result['complementarity']),np.array(result['coverage'])
            graph=result['graph']
            graph['cache_hit']=True
        else:
            comp,coverage,graph=build_evidence(query,relevance)
            payload=json.dumps({'complementarity':comp.tolist(),'coverage':coverage.tolist(),'graph':graph},sort_keys=True)
            db.execute('INSERT INTO graphs VALUES (?,?,?)',(key,hashlib.sha256(payload.encode()).hexdigest(),payload))
            graph['cache_hit']=False
    if comp.shape != (len(query.documents),len(query.documents)) or not np.isfinite(comp).all():
        raise ValueError('Invalid cached graph shape')
    graph['lookup_seconds']=perf_counter()-started
    return comp,coverage,graph
