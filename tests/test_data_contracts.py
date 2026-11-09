import unittest
from dataclasses import replace

from qrag.data import EvaluationLabels, adapt_example
from qrag.datasets import duplicate_audit, hotpot_record, musique_record, score_answer


class DataContracts(unittest.TestCase):
    def test_sentence_mapping_and_gold_isolation(self):
        raw = hotpot_record(
            {
                "id": "h",
                "question": "Where?",
                "answer": "India",
                "type": "bridge",
                "level": "easy",
                "context": {"title": ["A"], "sentences": [["First.", "Second."]]},
                "supporting_facts": {"title": ["A"], "sent_id": [1]},
            }
        )
        query, labels = adapt_example(raw)
        self.assertEqual(query.documents[0].sentences, ("First.", "Second."))
        self.assertEqual(labels.supporting_sentences, frozenset({("A", 1)}))
        raw["answer"] = "Nepal"
        self.assertEqual(adapt_example(raw)[0], query)
        raw["supporting_facts"]["details"][0]["sent_id"] = 9
        with self.assertRaisesRegex(ValueError, "sentence mapping"):
            adapt_example(raw)

    def test_musique_ids_distinguish_duplicate_titles(self):
        row = {
            "id": "m",
            "question": "Who?",
            "answer": "Maya",
            "answer_aliases": ["Maya Rao"],
            "paragraphs": [
                {
                    "idx": 7,
                    "title": "Film",
                    "paragraph_text": "Maya directed it.",
                    "is_supporting": True,
                },
                {
                    "idx": 9,
                    "title": "Film",
                    "paragraph_text": "Other text.",
                    "is_supporting": False,
                },
            ],
        }
        query, labels = adapt_example(musique_record(row))
        self.assertEqual(labels.supporting_ids, frozenset({"m:d0"}))
        self.assertEqual(query.documents[1].source_id, "9")
        self.assertEqual(score_answer("Maya Rao", labels)["answer_em"], 1)
        self.assertFalse(hasattr(query.documents[0], "is_supporting"))

    def test_dataset_metric_differences(self):
        hotpot = EvaluationLabels("yes", frozenset())
        musique = replace(hotpot, dataset="musique")
        self.assertEqual(score_answer("yes indeed", hotpot)["answer_f1"], 0)
        self.assertAlmostEqual(score_answer("yes indeed", musique)["answer_f1"], 2 / 3)
        self.assertEqual(
            score_answer("", replace(musique, answer="the"))["answer_f1"], 1
        )

    def test_duplicate_audit_finds_exact_and_near(self):
        dev = [{"id": "a", "question": "Who was the director of Film A in 1995?"}]
        evaluation = [
            {"id": "b", "question": "Who was the director of Film A in 1995!"},
            {"id": "c", "question": "What is the capital of India?"},
        ]
        audit = duplicate_audit(dev, evaluation)
        self.assertEqual([x["id"] for x in audit["matches"]], ["b"])


if __name__ == "__main__":
    unittest.main()
