import unittest
from qrag.evaluation import paired_interval,question_scores


class StatisticsTests(unittest.TestCase):
    def test_pairing_and_seed_aggregation(self):
        records=[{'question_id':'q','method':'method_s41','status':'success','metrics':{'answer_f1':1}},
                 {'question_id':'q','method':'method_s42','status':'error'}]
        self.assertEqual(question_scores(records),{'method':{'q':.5}})
        result=paired_interval({'q':.5,'r':.5},{'q':0.,'r':0.},resamples=100)
        self.assertEqual(result['ci95'],[.5,.5])
        with self.assertRaises(ValueError):paired_interval({'q':1},{'r':1})


if __name__=='__main__':unittest.main()
