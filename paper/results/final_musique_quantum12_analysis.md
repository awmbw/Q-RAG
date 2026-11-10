| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_full | 5 | 0.3000 | 0.4667 | 871.8000 | 0 |
| random_full | 5 | 0.2412 | 0.4833 | 863.7333 | 0 |
| xy_absolute_f0.5 | 5 | 0.1000 | 0.5444 | 783.2667 | 0 |
| xy_evidence_f0.5 | 5 | 0.0333 | 0.5111 | 735.1333 | 0 |
| xy_full_p1 | 5 | 0.0333 | 0.5278 | 789.0000 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| random_full | -0.0588 | [-0.2000, 0.0235] |
| xy_absolute_f0.5 | -0.2000 | [-0.6000, 0.0000] |
| xy_evidence_f0.5 | -0.2667 | [-0.6667, 0.0000] |
| xy_full_p1 | -0.2667 | [-0.6667, 0.0000] |
