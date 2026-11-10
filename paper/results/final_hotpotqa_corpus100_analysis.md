| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 30 | 0.2720 | 0.6000 | 788.0000 | 0 |
| coverage | 30 | 0.2848 | 0.7500 | 892.0667 | 0 |
| greedy | 30 | 0.3252 | 0.7000 | 793.1667 | 0 |
| hybrid | 30 | 0.2954 | 0.7167 | 832.1000 | 0 |
| milp_base | 30 | 0.3188 | 0.6833 | 798.2000 | 0 |
| milp_full | 30 | 0.2694 | 0.7333 | 808.8333 | 0 |
| reranker | 30 | 0.3316 | 0.8167 | 791.5667 | 0 |
| top_k | 30 | 0.2757 | 0.7500 | 811.4000 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| bm25 | 0.0026 | [-0.1122, 0.1189] |
| coverage | 0.0153 | [-0.0909, 0.1245] |
| greedy | 0.0557 | [-0.0831, 0.2016] |
| hybrid | 0.0260 | [-0.0561, 0.1240] |
| milp_base | 0.0494 | [-0.0630, 0.1778] |
| reranker | 0.0622 | [-0.0078, 0.1522] |
| top_k | 0.0063 | [-0.1111, 0.1229] |
