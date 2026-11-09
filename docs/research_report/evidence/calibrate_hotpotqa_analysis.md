| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| coverage | 100 | 0.6605 | 0.9350 | 795.4000 | 0 |
| milp_g0.0 | 100 | 0.6358 | 0.8900 | 792.2500 | 0 |
| milp_g0.1 | 100 | 0.6412 | 0.9150 | 794.8900 | 0 |
| milp_g0.2 | 100 | 0.6533 | 0.9200 | 791.4800 | 0 |
| milp_g0.4 | 100 | 0.6192 | 0.9150 | 806.7100 | 0 |
| milp_g0.8 | 100 | 0.5946 | 0.8550 | 804.7000 | 0 |
| top_k | 100 | 0.6162 | 0.8850 | 784.1700 | 0 |

Paired differences are method minus milp_g0.0; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| coverage | 0.0247 | [-0.0423, 0.0933] |
| milp_g0.1 | 0.0054 | [-0.0440, 0.0554] |
| milp_g0.2 | 0.0175 | [-0.0452, 0.0800] |
| milp_g0.4 | -0.0166 | [-0.0910, 0.0575] |
| milp_g0.8 | -0.0412 | [-0.1216, 0.0393] |
| top_k | -0.0196 | [-0.0802, 0.0397] |
