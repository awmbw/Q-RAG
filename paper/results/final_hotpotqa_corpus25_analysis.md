| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 100 | 0.3812 | 0.6600 | 853.8100 | 0 |
| coverage | 100 | 0.4420 | 0.8150 | 873.0600 | 0 |
| greedy | 100 | 0.3794 | 0.6950 | 822.7100 | 0 |
| hybrid | 100 | 0.4234 | 0.7600 | 825.8200 | 0 |
| milp_base | 100 | 0.3861 | 0.6850 | 808.0700 | 0 |
| milp_full | 100 | 0.4095 | 0.7450 | 816.1700 | 0 |
| reranker | 100 | 0.4221 | 0.8200 | 787.8600 | 0 |
| top_k | 100 | 0.4052 | 0.7500 | 795.3100 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | -0.0283 | [-0.1040, 0.0474] |
| coverage | 0.0325 | [-0.0179, 0.0854] |
| greedy | -0.0301 | [-0.0875, 0.0263] |
| hybrid | 0.0139 | [-0.0420, 0.0700] |
| milp_base | -0.0234 | [-0.0770, 0.0297] |
| reranker | 0.0126 | [-0.0543, 0.0794] |
| top_k | -0.0043 | [-0.0385, 0.0298] |
