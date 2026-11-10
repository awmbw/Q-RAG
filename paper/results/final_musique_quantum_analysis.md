| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_base | 50 | 0.3178 | 0.6500 | 784.9800 | 0 |
| milp_full | 50 | 0.3178 | 0.6300 | 794.8400 | 0 |
| penalty_absolute | 50 | 0.2667 | 0.6283 | 770.4600 | 0 |
| penalty_evidence | 50 | 0.2644 | 0.6283 | 776.7000 | 0 |
| penalty_full | 50 | 0.2919 | 0.6367 | 798.3733 | 0 |
| random_full | 50 | 0.3178 | 0.6300 | 794.8400 | 0 |
| xy_absolute_f0.5 | 50 | 0.2399 | 0.5128 | 779.0000 | 0 |
| xy_degree_f0.5 | 50 | 0.2426 | 0.5311 | 780.6733 | 0 |
| xy_evidence_f0.5 | 50 | 0.2304 | 0.5072 | 767.7000 | 0 |
| xy_full_p1 | 50 | 0.2418 | 0.5311 | 782.9800 | 0 |
| xy_full_p2 | 50 | 0.2436 | 0.5711 | 780.8600 | 0 |
| xy_random_f0.5 | 50 | 0.2405 | 0.5283 | 775.4067 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| milp_base | 0.0000 | [-0.0600, 0.0600] |
| penalty_absolute | -0.0511 | [-0.1356, 0.0267] |
| penalty_evidence | -0.0533 | [-0.1400, 0.0200] |
| penalty_full | -0.0259 | [-0.0733, 0.0141] |
| random_full | 0.0000 | [0.0000, 0.0000] |
| xy_absolute_f0.5 | -0.0779 | [-0.1851, 0.0244] |
| xy_degree_f0.5 | -0.0752 | [-0.1867, 0.0351] |
| xy_evidence_f0.5 | -0.0873 | [-0.1991, 0.0182] |
| xy_full_p1 | -0.0759 | [-0.1760, 0.0156] |
| xy_full_p2 | -0.0742 | [-0.1642, 0.0056] |
| xy_random_f0.5 | -0.0773 | [-0.1681, 0.0071] |
