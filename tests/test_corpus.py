import unittest

from qrag.corpus import corpus_id, deduplicate
from qrag.data import Document, adapt_example
from qrag.datasets import score_evidence


class CorpusTests(unittest.TestCase):
    def test_content_identity_and_retrieval_miss_remains_evaluable(self):
        docs = [Document("a", "Title", "Text."), Document("b", "Title", "Text.")]
        self.assertEqual(len(deduplicate(docs)), 1)
        self.assertEqual(deduplicate(docs)[0].id, corpus_id("Title", "Text."))
        raw = {
            "id": "q",
            "question": "Who?",
            "answer": "Maya",
            "candidate_source": "retrieved",
            "documents": [{"id": "c", "title": "Wrong", "text": "Other."}],
            "supporting_facts": {"titles": ["Missing"]},
            "supporting_ids": ["absent"],
        }
        query, labels = adapt_example(raw)
        self.assertEqual(score_evidence(query.documents, labels)["document_recall"], 0)
        raw.pop("candidate_source")
        with self.assertRaises(ValueError):
            adapt_example(raw)


if __name__ == "__main__":
    unittest.main()
