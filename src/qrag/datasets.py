"""Primary-dataset adapters and deterministic, label-independent split selection."""
from collections import Counter
import re

from qrag.data import adapt_example
from qrag.metrics import answer_metrics, normalize_answer


def hotpot_record(row: dict) -> dict:
    titles = row['context']['title']
    sentences = row['context']['sentences']
    support = row['supporting_facts']
    return {
        'id': row['id'], 'question': row['question'], 'answer': row['answer'],
        'dataset': 'hotpotqa', 'type': row['type'], 'level': row['level'],
        'documents': [{'title': title, 'sentences': sents, 'text': ' '.join(sents)}
                      for title, sents in zip(titles, sentences, strict=True)],
        'supporting_facts': {'titles': sorted(set(support['title'])),
                            'details': [{'title': t, 'sent_id': s} for t, s in
                                        zip(support['title'], support['sent_id'], strict=True)]},
    }


def musique_record(row: dict) -> dict:
    if not row.get('answerable', True):
        raise ValueError('Only MuSiQue-Ans answerable examples are supported')
    documents = [{'title': p['title'], 'text': p['paragraph_text'],
                  'source_id': str(p['idx'])} for p in row['paragraphs']]
    ids = [f"{row['id']}:d{i}" for i, p in enumerate(row['paragraphs']) if p['is_supporting']]
    return {'id': row['id'], 'question': row['question'], 'answer': row['answer'],
            'answer_aliases': row.get('answer_aliases', []), 'dataset': 'musique',
            'documents': documents, 'supporting_ids': ids,
            'supporting_facts': {'titles': sorted({p['title'] for p in row['paragraphs'] if p['is_supporting']})}}


def score_answer(prediction: str, labels) -> dict:
    if labels.dataset == 'hotpotqa':
        return answer_metrics(prediction, labels.answer)
    # MuSiQue uses SQuAD-style alias maxima; no Hotpot yes/no exception.
    from collections import Counter
    def pair(reference):
        p, g = normalize_answer(prediction).split(), normalize_answer(reference).split()
        overlap = sum((Counter(p) & Counter(g)).values())
        f1 = float(p == g) if not p or not g else 2 * overlap / (len(p) + len(g))
        return float(p == g), f1
    scores = [pair(reference) for reference in (labels.answer, *labels.aliases)]
    return {'answer_em': max(s[0] for s in scores), 'answer_f1': max(s[1] for s in scores)}


def score_evidence(selected, labels) -> dict:
    gold = labels.supporting_ids or labels.supporting_titles
    predicted = {d.id for d in selected} if labels.supporting_ids else {d.title for d in selected}
    overlap = len(predicted & gold)
    return {'document_recall': overlap / len(gold) if gold else None,
            'document_precision': overlap / len(predicted) if predicted else 0.,
            'all_supporting_documents': float(gold <= predicted) if gold else None}


def question_key(text: str) -> str:
    return ' '.join(re.findall(r'\w+', text.casefold()))


def shingles(text: str) -> frozenset[str]:
    words = question_key(text).split()
    return frozenset(' '.join(words[i:i+3]) for i in range(max(1, len(words)-2)))


def duplicate_audit(development: list[dict], evaluation: list[dict], threshold=.8) -> dict:
    """Exact normalized questions plus token-trigram Jaccard; not a contamination proof."""
    seen = {}
    inverted = {}
    for row in development:
        terms = shingles(row['question'])
        seen[row['id']] = terms
        for term in terms:
            inverted.setdefault(term, set()).add(row['id'])
    matches = []
    exact = {question_key(row['question']) for row in development}
    for row in evaluation:
        terms = shingles(row['question'])
        candidates = set().union(*(inverted.get(t, set()) for t in terms))
        similarities = [(q, len(terms & seen[q]) / max(1, len(terms | seen[q]))) for q in candidates]
        near = [(q, score) for q, score in similarities if score >= threshold]
        if near or question_key(row['question']) in exact:
            matches.append({'id': row['id'], 'matches': sorted(near),
                            'exact': question_key(row['question']) in exact})
    return {'threshold': threshold, 'method': 'normalized question exact + word trigram Jaccard',
            'matches': matches, 'limitations': 'Does not detect paraphrase or pretrained-model contamination.'}


def validate_records(records: list[dict]) -> dict:
    counts = Counter()
    ids = set()
    for row in records:
        query, labels = adapt_example(row)
        if query.id in ids:
            raise ValueError('duplicate query ID')
        ids.add(query.id)
        counts['questions'] += 1
        counts['documents'] += len(query.documents)
        counts['supporting_sentence_annotations'] += len(labels.supporting_sentences)
        counts['answer_aliases'] += len(labels.aliases)
    return dict(counts)
