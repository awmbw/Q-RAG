from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from qrag.optimization import SelectionProblem,select_exhaustive
from qrag.sparsification import sparsify
from qrag.experiments.journal import JournalRunStore


class SparsificationTests(unittest.TestCase):
    def test_edge_budgets_signs_and_gap_bound(self):
        rng=np.random.default_rng(4)
        problem=SelectionProblem(rng.normal(size=6),np.triu(rng.normal(size=(6,6)),1),3)
        comp=rng.random((6,6))
        full=select_exhaustive(problem)
        for rule in ('absolute','random','degree','evidence'):
            sparse,meta=sparsify(problem,comp,rule,.5)
            self.assertEqual(np.count_nonzero(sparse.pairs),7)
            retained=sparse.pairs!=0
            np.testing.assert_array_equal(sparse.pairs[retained],problem.pairs[retained])
            optimum=select_exhaustive(sparse)
            self.assertLessEqual(problem.energy(optimum.indices)-full.energy,2*meta['removed_l1']+1e-10)
            self.assertEqual(sparse.k,problem.k)

    def test_zero_and_full_masks_and_seed(self):
        p=SelectionProblem(np.array([-1.,-.5,-.3]),np.triu(np.ones((3,3)),1),1)
        for fraction in (0,1):
            s,m=sparsify(p,np.eye(3),'evidence',fraction)
            self.assertEqual(np.count_nonzero(s.pairs),int(fraction*3))
        a,_=sparsify(p,np.eye(3),'random',.5,9);b,_=sparsify(p,np.eye(3),'random',.5,9)
        np.testing.assert_array_equal(a.pairs,b.pairs)


class JournalTests(unittest.TestCase):
    def test_retry_and_torn_tail_recovery(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'run';store=JournalRunStore(path,{'config':1})
            store.save_record({'question_id':'q','method':'m','status':'error'})
            with (path/'predictions.jsonl').open('ab') as handle:handle.write(b'{"partial":')
            resumed=JournalRunStore(path,{'config':1},True)
            self.assertTrue((path/'recovered_partial_tail.bin').exists())
            resumed.save_record({'question_id':'q','method':'m','status':'success'})
            final=JournalRunStore(path,{'config':1},True)
            self.assertEqual(final.records[('q','m')]['attempt'],2)
            with self.assertRaises(ValueError):final.save_record({'question_id':'q','method':'m','status':'success'})

    def test_resume_mismatch_does_not_modify_tail(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'run';JournalRunStore(path,{'x':1})
            tail=path/'predictions.jsonl';tail.write_bytes(b'{partial')
            with self.assertRaisesRegex(ValueError,'identity'):
                JournalRunStore(path,{'x':2},True)
            self.assertEqual(tail.read_bytes(),b'{partial')


if __name__=='__main__':
    unittest.main()
