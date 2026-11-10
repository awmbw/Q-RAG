| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_base | 50 | 0.3432 | 0.8400 | 820.7600 | 0 |
| milp_full | 50 | 0.3311 | 0.8500 | 808.6400 | 0 |
| penalty_absolute | 50 | 0.3200 | 0.7867 | 833.7067 | 0 |
| penalty_evidence | 50 | 0.3013 | 0.8067 | 828.0867 | 0 |
| penalty_full | 50 | 0.3079 | 0.8389 | 813.9329 | 1 |
| random_full | 50 | 0.3378 | 0.8500 | 807.7333 | 0 |
| xy_absolute_f0.5 | 50 | 0.3490 | 0.7267 | 811.4733 | 0 |
| xy_degree_f0.5 | 50 | 0.3384 | 0.7400 | 817.8400 | 0 |
| xy_evidence_f0.5 | 50 | 0.3128 | 0.7233 | 813.9800 | 0 |
| xy_full_p1 | 50 | 0.3379 | 0.7467 | 819.8267 | 0 |
| xy_full_p2 | 50 | 0.3051 | 0.7767 | 815.5333 | 0 |
| xy_random_f0.5 | 50 | 0.2875 | 0.7033 | 819.4933 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| milp_base | 0.0121 | [-0.0700, 0.0919] |
| penalty_absolute | -0.0111 | [-0.0485, 0.0249] |
| penalty_evidence | -0.0298 | [-0.0911, 0.0204] |
| penalty_full | -0.0232 | [-0.0709, 0.0202] |
| random_full | 0.0067 | [0.0000, 0.0200] |
| xy_absolute_f0.5 | 0.0179 | [-0.0678, 0.1093] |
| xy_degree_f0.5 | 0.0073 | [-0.0855, 0.1037] |
| xy_evidence_f0.5 | -0.0183 | [-0.1122, 0.0769] |
| xy_full_p1 | 0.0068 | [-0.0893, 0.1068] |
| xy_full_p2 | -0.0260 | [-0.1159, 0.0648] |
| xy_random_f0.5 | -0.0436 | [-0.1369, 0.0483] |
