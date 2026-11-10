| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_full | 5 | 0.3000 | 0.4667 | 893.4000 | 0 |
| random_full | 5 | 0.1745 | 0.5500 | 837.6667 | 0 |
| xy_absolute_f0.5 | 5 | 0.0626 | 0.3500 | 768.5333 | 0 |
| xy_evidence_f0.5 | 5 | 0.0857 | 0.3500 | 776.0000 | 0 |
| xy_full_p1 | 5 | 0.0857 | 0.3500 | 777.4667 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| random_full | -0.1255 | [-0.4000, 0.0235] |
| xy_absolute_f0.5 | -0.2374 | [-0.6374, 0.0381] |
| xy_evidence_f0.5 | -0.2143 | [-0.6143, 0.0381] |
| xy_full_p1 | -0.2143 | [-0.6143, 0.0381] |
