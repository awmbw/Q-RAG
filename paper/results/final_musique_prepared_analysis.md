| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_base | 50 | 0.3178 | 0.6500 | 784.9800 | 0 |
| milp_full | 50 | 0.3178 | 0.6300 | 794.8400 | 0 |
| prepared_absolute_f0.5 | 50 | 0.2533 | 0.6139 | 763.7667 | 0 |
| prepared_base_p1 | 50 | 0.2725 | 0.6300 | 764.1400 | 0 |
| prepared_evidence_f0.5 | 50 | 0.2636 | 0.6050 | 771.9200 | 0 |
| prepared_full_p1 | 50 | 0.2606 | 0.6128 | 785.1933 | 0 |
| prepared_full_p2 | 50 | 0.2885 | 0.6411 | 789.3600 | 0 |
| random_full | 50 | 0.3178 | 0.6300 | 794.8400 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| milp_base | 0.0000 | [-0.0600, 0.0600] |
| prepared_absolute_f0.5 | -0.0644 | [-0.1456, 0.0067] |
| prepared_base_p1 | -0.0453 | [-0.1105, 0.0133] |
| prepared_evidence_f0.5 | -0.0541 | [-0.1335, 0.0153] |
| prepared_full_p1 | -0.0572 | [-0.1249, -0.0010] |
| prepared_full_p2 | -0.0293 | [-0.0885, 0.0174] |
| random_full | 0.0000 | [0.0000, 0.0000] |
