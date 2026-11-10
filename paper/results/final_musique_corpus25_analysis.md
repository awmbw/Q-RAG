| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 100 | 0.1200 | 0.3692 | 816.9300 | 0 |
| coverage | 100 | 0.2264 | 0.5358 | 814.4500 | 0 |
| greedy | 100 | 0.1510 | 0.4583 | 764.8000 | 0 |
| hybrid | 100 | 0.2055 | 0.5125 | 799.9700 | 0 |
| milp_base | 100 | 0.1578 | 0.4525 | 740.6900 | 0 |
| milp_full | 100 | 0.1751 | 0.4942 | 791.4300 | 0 |
| reranker | 100 | 0.1746 | 0.5392 | 780.7800 | 0 |
| top_k | 100 | 0.1604 | 0.5008 | 775.6400 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | -0.0551 | [-0.1247, 0.0131] |
| coverage | 0.0513 | [-0.0080, 0.1130] |
| greedy | -0.0241 | [-0.0836, 0.0337] |
| hybrid | 0.0304 | [-0.0336, 0.0968] |
| milp_base | -0.0174 | [-0.0737, 0.0375] |
| reranker | -0.0006 | [-0.0661, 0.0682] |
| top_k | -0.0147 | [-0.0652, 0.0337] |
