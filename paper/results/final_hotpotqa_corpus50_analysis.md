| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 30 | 0.2421 | 0.6167 | 838.4333 | 0 |
| coverage | 30 | 0.2754 | 0.7500 | 884.6667 | 0 |
| greedy | 30 | 0.3252 | 0.7000 | 800.5000 | 0 |
| hybrid | 30 | 0.3112 | 0.7167 | 843.7667 | 0 |
| milp_base | 30 | 0.3188 | 0.6833 | 799.2000 | 0 |
| milp_full | 30 | 0.2806 | 0.7333 | 817.8000 | 0 |
| reranker | 30 | 0.3316 | 0.8167 | 798.5000 | 0 |
| top_k | 30 | 0.2757 | 0.7500 | 811.4000 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | -0.0385 | [-0.1473, 0.0754] |
| coverage | -0.0052 | [-0.1171, 0.1099] |
| greedy | 0.0446 | [-0.0879, 0.1827] |
| hybrid | 0.0306 | [-0.0502, 0.1258] |
| milp_base | 0.0382 | [-0.0652, 0.1583] |
| reranker | 0.0511 | [-0.0233, 0.1422] |
| top_k | -0.0049 | [-0.1138, 0.0965] |
