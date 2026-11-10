| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 30 | 0.0833 | 0.3028 | 809.6667 | 0 |
| coverage | 30 | 0.1690 | 0.4972 | 877.7333 | 0 |
| greedy | 30 | 0.0833 | 0.4250 | 767.3333 | 0 |
| hybrid | 30 | 0.1357 | 0.4556 | 834.4333 | 0 |
| milp_base | 30 | 0.1524 | 0.4028 | 755.7333 | 0 |
| milp_full | 30 | 0.1000 | 0.4639 | 789.9000 | 0 |
| reranker | 30 | 0.1278 | 0.5194 | 783.9000 | 0 |
| top_k | 30 | 0.1333 | 0.4639 | 819.7667 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | -0.0167 | [-0.1167, 0.0833] |
| coverage | 0.0690 | [-0.0167, 0.1833] |
| greedy | -0.0167 | [-0.0500, 0.0000] |
| hybrid | 0.0357 | [0.0000, 0.1048] |
| milp_base | 0.0524 | [0.0000, 0.1357] |
| reranker | 0.0278 | [-0.0167, 0.1000] |
| top_k | 0.0333 | [0.0000, 0.0833] |
