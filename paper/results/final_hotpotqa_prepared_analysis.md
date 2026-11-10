| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| milp_base | 50 | 0.3432 | 0.8400 | 820.7600 | 0 |
| milp_full | 50 | 0.3311 | 0.8500 | 808.6400 | 0 |
| prepared_absolute_f0.5 | 50 | 0.2903 | 0.7700 | 838.1667 | 0 |
| prepared_base_p1 | 50 | 0.3291 | 0.8167 | 816.2333 | 0 |
| prepared_evidence_f0.5 | 50 | 0.3055 | 0.7867 | 821.7000 | 0 |
| prepared_full_p1 | 50 | 0.2922 | 0.8200 | 801.7867 | 0 |
| prepared_full_p2 | 50 | 0.3134 | 0.8467 | 797.3933 | 0 |
| random_full | 50 | 0.3378 | 0.8500 | 807.7333 | 0 |

Paired differences are method minus milp_full; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| milp_base | 0.0121 | [-0.0700, 0.0919] |
| prepared_absolute_f0.5 | -0.0408 | [-0.1098, 0.0252] |
| prepared_base_p1 | -0.0020 | [-0.0978, 0.0935] |
| prepared_evidence_f0.5 | -0.0257 | [-0.0989, 0.0399] |
| prepared_full_p1 | -0.0389 | [-0.0953, 0.0111] |
| prepared_full_p2 | -0.0177 | [-0.0566, 0.0170] |
| random_full | 0.0067 | [0.0000, 0.0200] |
