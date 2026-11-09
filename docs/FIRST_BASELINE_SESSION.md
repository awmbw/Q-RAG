**First implementation session — November 4, 2026**

Implemented an installable qrag package, strict TOML configuration, separate inference/evaluation objects, answer/document metrics, fixed-count top-k and MILP, real local model adapters, manifests/predictions, failure handling, guarded resume and offline correctness tests. The new baseline runner uses classical methods. Graph features, token-budget selection and QAOA experiments remain later milestones.

**Validation performed**

- Seventeen offline tests passed, including MILP/exhaustive agreement across tiny signed-pair instances and k=0/k=n boundaries, gold-label isolation, HotpotQA answer-metric fixtures, nonoptimal/incumbent handling, partial/complete resume, changed-config/data rejection and failure denominators.
- Editable package installation succeeded without downloads.
- A real offline MiniLM/Qwen run completed on the first three development questions, with two methods per question. All six method/question records succeeded and selected exactly five documents. No embedding truncation or output-token-limit hit occurred.
- The experiment used cached immutable model snapshots, CPU float32 inference and four PyTorch threads. Model preparation took approximately 4.72 seconds; the recorded invocation took approximately 61.32 seconds. These are local observations, not a latency guarantee or quantum measurement.

Local artifacts: results/baseline_dev_001/manifest.json, predictions.jsonl and summary.json. That directory is intentionally ignored by Git; the observed smoke results below are preserved in this tracked note.

| Metric, three inspected development questions | Top-k | MILP |
| --- | ---: | ---: |
| Successful records | 3/3 | 3/3 |
| Mean selected documents | 5 | 5 |
| Answer exact match | 0.3333 | 0.3333 |
| Answer token F1 | 0.3333 | 0.3333 |
| Supporting-document recall | 0.6667 | 0.8333 |
| All annotated supporting documents selected | 0.3333 | 0.6667 |
| Mean context tokens | 615.33 | 710.00 |

MILP obtained a lower full-objective energy than ranking on each of these instances. This validates that the pipeline can distinguish optimization, evidence and answer metrics; three development examples do not establish method superiority. Token consumption is unequal despite equal document counts. All three MILP results reported optimal status for their specified constrained objectives.

**Error-analysis observations**

1. Question 5abed9f45542994516f4545a: both methods answered Rosie Mac, matching the reference.
2. Question 5ab1dd6c5542993be8fa9860: the reference is Romantic; top-k generated Romanticism and MILP generated Modernismo. Both receive zero answer token F1 under the official normalization rules. The first answer illustrates a semantic near-match that token metrics do not capture; the second requires separate evidence/generation analysis. Do not change scoring to improve a preferred method's result.
3. Question 5adfa059554299025d62a2f8 asks for a 1995 film but its reference answer is Richard E. Grant. Both methods generated Jack and Sarah. A read-only check of the matching record in the cached upstream HotpotQA train Arrow shard confirmed the same question/reference pair, so this inconsistency was not introduced by our JSON adapter. Preserve the reference in the primary score, flag it for data-quality review and avoid claiming the generated answer was wrong solely from this mismatch. This is one checked annotation anomaly, not an estimate of dataset-wide label quality.

**What to learn from this slice**

The same document-count budget prevents the previous count imbalance, but a separate token-budget experiment is still needed. Exact objective optimization does not guarantee better generated answers. Automated answer metrics require error analysis, and annotated references can be imperfect. The experiment manifest records what actually ran so these observations can be traced rather than inferred from filenames.
