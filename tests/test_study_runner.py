from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from qrag.config import ExperimentConfig
from qrag.experiments.study import run_study


class FakeModel:
    device='cpu'
    embedder=None
    def __init__(self,fail=False):self.prepared=0;self.generated=0;self.fail=fail
    def prepare(self):self.prepared+=1;return {'kind':'offline_test_double'}
    def generate(self,query,selected):
        self.generated+=1
        if self.fail:raise RuntimeError('test generation failure')
        return {'answer':'India','context_tokens':20,'input_tokens':30,'input_ids':[1]*30,
                'output_tokens':1,'generation_seconds':.01,'prompt':'test prompt'}


class StudyRunnerTests(unittest.TestCase):
    def test_generation_reuse_and_error_retry(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);data=root/'data.json'
            data.write_text(json.dumps([{'id':'q','question':'Where?','answer':'India',
                'documents':[{'title':'A','text':'India.'},{'title':'B','text':'Nepal.'}],
                'supporting_facts':{'titles':['A']}}]))
            config=ExperimentConfig(dataset=str(data),limit=1,k=1).as_dict()
            spec={'model':config,'methods':[{'name':'top_k','solver':'top_k'},{'name':'milp','solver':'milp'}]}
            encoder=SimpleNamespace(score=lambda q:(np.array([.8,.4]),np.eye(2),{}),cache=SimpleNamespace(close=lambda:None))
            features=(np.zeros((2,2)),np.ones((2,1)),{})
            with patch('qrag.experiments.study.ChunkEncoder',return_value=encoder),patch('qrag.experiments.study.cached_evidence',return_value=features),patch('qrag.experiments.study.bm25_scores',return_value=np.zeros(2)),redirect_stdout(StringIO()):
                failed=run_study(spec,root/'run',backend=FakeModel(True))
                self.assertEqual(failed['methods']['milp']['failures'],1)
                model=FakeModel()
                success=run_study(spec,root/'run',True,backend=model)
                self.assertEqual(success['methods']['milp']['answer_f1'],1)
                self.assertEqual(model.generated,1)
                unused=FakeModel()
                run_study(spec,root/'run',True,backend=unused)
                self.assertEqual(unused.prepared,0)
            attempts=[json.loads(l) for l in (root/'run/predictions.jsonl').read_text().splitlines()]
            self.assertEqual(len(attempts),4)
            self.assertTrue(all(r['attempt']==2 for r in attempts[-2:]))


if __name__=='__main__':unittest.main()
