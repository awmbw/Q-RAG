| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 30 | 0.0833 | 0.2972 | 855.9667 | 0 |
| coverage | 30 | 0.1611 | 0.5000 | 882.8667 | 0 |
| greedy | 30 | 0.1000 | 0.4417 | 776.1333 | 0 |
| hybrid | 30 | 0.1357 | 0.4556 | 831.0000 | 0 |
| milp_base | 30 | 0.1554 | 0.4111 | 778.4000 | 0 |
| milp_full | 30 | 0.1167 | 0.4806 | 820.0333 | 0 |
| reranker | 30 | 0.1111 | 0.5472 | 792.5000 | 0 |
| top_k | 30 | 0.1333 | 0.4639 | 819.7667 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | -0.0333 | [-0.1500, 0.0833] |
| coverage | 0.0444 | [-0.0722, 0.1667] |
| greedy | -0.0167 | [-0.1000, 0.0500] |
| hybrid | 0.0190 | [-0.0786, 0.1190] |
| milp_base | 0.0387 | [-0.0636, 0.1411] |
| reranker | -0.0056 | [-0.1056, 0.0944] |
| top_k | 0.0167 | [-0.0833, 0.1000] |
