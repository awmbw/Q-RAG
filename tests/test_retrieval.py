import importlib.util
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
import numpy as np

from qrag.data import Document
from qrag.retrieval import chunk_document, EmbeddingCache, ExactIndex, reciprocal_rank_fusion


class WordTokenizer:
    def __call__(self, text, add_special_tokens=True, return_offsets_mapping=False):
        spans = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
        result = {'input_ids': list(range(len(spans) + (2 if add_special_tokens else 0)))}
        if return_offsets_mapping:
            result['offset_mapping'] = spans
        return result

    def decode(self, ids, **kwargs):
        return ' '.join('title' for _ in ids)


class RetrievalTests(unittest.TestCase):
    def test_long_sentence_offsets_and_no_text_loss(self):
        text = ' '.join(f'word{i}' for i in range(100)) + '.'
        doc = Document('d', 'Title', text, (text,))
        tokenizer = WordTokenizer()
        chunks = chunk_document(doc, tokenizer, max_tokens=24, overlap=4)
        covered = set()
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c.text, text[c.start:c.end])
            self.assertLessEqual(len(tokenizer(c.embedding_text)['input_ids']), 24)
            covered.update(range(c.start, c.end))
            self.assertEqual(c.sentence_ids, (0,))
        self.assertTrue(all(i in covered for i, char in enumerate(text) if not char.isspace()))

    def test_cache_identity_and_corruption(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.sqlite'
            a = EmbeddingCache(path, {'revision': 'one'})
            self.assertIsNone(a.get('text'))
            a.put('text', [1., 0.])
            np.testing.assert_array_equal(a.get('text'), [1, 0])
            self.assertIsNone(a.get('text', 'query'))
            b = EmbeddingCache(path, {'revision': 'two'})
            self.assertIsNone(b.get('text'))
            with a.connection:
                a.connection.execute("UPDATE embeddings SET value=x'0000'")
            with self.assertRaises(ValueError):
                a.get('text')
            a.close(); b.close()

    def test_rank_fusion_stable(self):
        scores = reciprocal_rank_fusion(np.array([3., 1, 2]), np.array([0., 2, 1]))
        self.assertAlmostEqual(scores[0], 1/61 + 1/63)
        self.assertAlmostEqual(scores[2], 2/62)

    @unittest.skipUnless(importlib.util.find_spec('faiss'), 'optional faiss not installed')
    def test_restored_index_and_identity_checks(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'index'
            chunks = [chunk_document(Document(str(i), 'T', f'Word{i}.'), WordTokenizer(), 24, overlap=4)[0] for i in range(2)]
            index = ExactIndex.build(path, chunks, np.eye(2), {'revision': 'a'})
            restored = ExactIndex(path, {'revision': 'a'})
            self.assertEqual(index.search([1, 0]), restored.search([1, 0]))
            with self.assertRaisesRegex(ValueError, 'identity'):
                ExactIndex(path, {'revision': 'b'})
            with (path / 'vectors.faiss').open('ab') as stream:
                stream.write(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                ExactIndex(path)


if __name__ == '__main__':
    unittest.main()
