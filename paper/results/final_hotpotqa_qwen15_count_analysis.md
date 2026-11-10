| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| annealing_full | 500 | 0.4517 | 0.8340 | 781.2340 | 0 |
| bm25 | 500 | 0.4737 | 0.7830 | 830.7440 | 0 |
| coverage | 500 | 0.4944 | 0.8790 | 790.9920 | 0 |
| greedy | 500 | 0.4523 | 0.8260 | 783.0040 | 0 |
| hybrid | 500 | 0.4568 | 0.8420 | 798.2680 | 0 |
| milp_absolute_f0.5 | 500 | 0.4595 | 0.8140 | 786.5360 | 0 |
| milp_absolute_f0.75 | 500 | 0.4431 | 0.8290 | 786.6720 | 0 |
| milp_base | 500 | 0.4546 | 0.8230 | 783.8360 | 0 |
| milp_evidence_f0.5 | 500 | 0.4546 | 0.8070 | 791.5560 | 0 |
| milp_evidence_f0.75 | 500 | 0.4666 | 0.8300 | 788.2620 | 0 |
| milp_full | 500 | 0.4517 | 0.8340 | 781.2340 | 0 |
| mmr | 500 | 0.4275 | 0.8050 | 784.6980 | 0 |
| random_full | 500 | 0.4520 | 0.8337 | 781.1287 | 0 |
| reranker | 500 | 0.4538 | 0.8550 | 768.7020 | 0 |
| top_k | 500 | 0.4402 | 0.8180 | 775.3820 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| annealing_full | 0.0000 | [0.0000, 0.0000] |
| bm25 | 0.0220 | [-0.0145, 0.0591] |
| coverage | 0.0427 | [0.0150, 0.0714] |
| greedy | 0.0006 | [-0.0256, 0.0264] |
| hybrid | 0.0051 | [-0.0258, 0.0363] |
| milp_absolute_f0.5 | 0.0077 | [-0.0113, 0.0269] |
| milp_absolute_f0.75 | -0.0087 | [-0.0241, 0.0066] |
| milp_base | 0.0029 | [-0.0237, 0.0288] |
| milp_evidence_f0.5 | 0.0028 | [-0.0178, 0.0230] |
| milp_evidence_f0.75 | 0.0148 | [-0.0033, 0.0332] |
| mmr | -0.0242 | [-0.0485, 0.0002] |
| random_full | 0.0003 | [-0.0024, 0.0031] |
| reranker | 0.0020 | [-0.0295, 0.0353] |
| top_k | -0.0115 | [-0.0352, 0.0126] |
