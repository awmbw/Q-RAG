| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| annealing_full | 100 | 0.1892 | 0.7131 | 1068.1300 | 0 |
| bm25 | 100 | 0.1738 | 0.5867 | 1089.8200 | 0 |
| coverage | 100 | 0.2086 | 0.7000 | 1091.6600 | 0 |
| greedy | 100 | 0.2151 | 0.6867 | 1053.3000 | 0 |
| hybrid | 100 | 0.1862 | 0.6700 | 1093.0900 | 0 |
| milp_absolute_f0.5 | 100 | 0.1597 | 0.6900 | 1086.9400 | 0 |
| milp_absolute_f0.75 | 100 | 0.1984 | 0.7342 | 1076.6200 | 0 |
| milp_base | 100 | 0.2161 | 0.6917 | 1055.5500 | 0 |
| milp_evidence_f0.5 | 100 | 0.1820 | 0.6742 | 1088.0600 | 0 |
| milp_evidence_f0.75 | 100 | 0.1834 | 0.7308 | 1075.9500 | 0 |
| milp_full | 100 | 0.1674 | 0.7175 | 1070.8700 | 0 |
| mmr | 100 | 0.1968 | 0.6800 | 1083.7000 | 0 |
| reranker | 100 | 0.2067 | 0.6942 | 1090.6300 | 0 |
| top_k | 100 | 0.1992 | 0.6825 | 1090.7100 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| annealing_full | 0.0218 | [-0.0037, 0.0517] |
| bm25 | 0.0064 | [-0.0454, 0.0613] |
| coverage | 0.0412 | [-0.0114, 0.0992] |
| greedy | 0.0477 | [-0.0073, 0.1068] |
| hybrid | 0.0188 | [-0.0390, 0.0818] |
| milp_absolute_f0.5 | -0.0077 | [-0.0638, 0.0494] |
| milp_absolute_f0.75 | 0.0310 | [0.0000, 0.0700] |
| milp_base | 0.0487 | [-0.0088, 0.1105] |
| milp_evidence_f0.5 | 0.0146 | [-0.0456, 0.0734] |
| milp_evidence_f0.75 | 0.0160 | [-0.0130, 0.0500] |
| mmr | 0.0294 | [-0.0274, 0.0874] |
| reranker | 0.0393 | [-0.0136, 0.0988] |
| top_k | 0.0318 | [-0.0230, 0.0896] |
