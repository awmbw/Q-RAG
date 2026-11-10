| Method | Questions | Answer F1 | Evidence recall | Actual context tokens | Failed records |
| --- | ---: | ---: | ---: | ---: | ---: |
| gate_absolute | 10 | 0.2033 | 0.5250 | 721.9000 | 0 |
| gate_evidence | 10 | 0.2167 | 0.5000 | 727.9333 | 0 |
| gate_penalty_control | 10 | 0.0000 | — | — | 10 |

Paired differences are method minus gate_absolute; 95% question bootstrap intervals.

| Method | Mean F1 difference | 95% interval |
| --- | ---: | --- |
| gate_evidence | 0.0133 | [-0.0100, 0.0500] |
| gate_penalty_control | -0.2033 | [-0.4333, -0.0100] |
