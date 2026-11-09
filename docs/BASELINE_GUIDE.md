**First baseline runner**

This is the first implemented research slice: fixed-count relevance ranking versus MILP on the same candidate pools, followed by local answer generation. Graph features, QAOA experiments, token-budget selection, chunking, persistent embedding caches and corpus search are later milestones. The legacy modules remain available separately.

**Environment and installation**

Run commands from the repository root. The tested local environment uses Python 3.14.4, NumPy 2.5.3, SciPy 1.18.1, PyTorch 2.14.0+cu132, Transformers 5.17.0 and SentenceTransformers 6.1.0. CUDA was unavailable through this execution environment; the smoke experiment ran on CPU with four PyTorch threads and float32 weights. A CUDA-enabled PyTorch build does not imply that a usable GPU is visible.

For the existing environment:

```bash
venv/bin/python -m pip install --no-deps --no-build-isolation -e .
venv/bin/python -m unittest discover -s tests -v
```

For a fresh environment with Python 3.14:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-baselines.lock
.venv/bin/python -m pip install -e '.[models]'
.venv/bin/python -m unittest discover -s tests -v
```

The core lock pins the tested NumPy/SciPy pair. The fresh model installation resolves its own runtime dependencies; compare them with the recorded environment before trying to reproduce a particular result. Manifests capture tested runtime versions. A portable model/GPU dependency lock is not yet supplied. The existing broad requirements.txt serves the legacy notebooks.

The real experiment requires the existing processed development JSON and the exact model snapshots configured in configs/dev_baselines.toml. The CLI defaults to local-only model resolution. If a snapshot is unavailable, obtain the specified model revision before running; the offline command will fail rather than quietly download or substitute another revision. Unit tests need neither models nor the real dataset.

**Run and inspect**

```bash
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false venv/bin/python -m qrag.experiments.run \
  --config configs/dev_baselines.toml --output results/my_baseline_run
```

Use a new output directory for a new run. To resume an interrupted run or recreate the summary from an already completed run:

```bash
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false venv/bin/python -m qrag.experiments.run \
  --config configs/dev_baselines.toml --output results/my_baseline_run --resume
```

Resume rejects changes in computation configuration, dataset bytes, question IDs, package source, recorded environment or backend identity. Completed records, including recorded per-method failures, are not retried or duplicated. After correcting a failure, use a new run directory. Saved records are atomically replaced after each method so interruption cannot leave a half-written JSON line. Do not run concurrent writers against one directory.

**Artifacts**

| Artifact | Contents |
| --- | --- |
| manifest.json | Actual configuration, dataset/source hashes, question IDs, pinned model snapshots, runtime packages/device, Git state, model preparation and invocation timing |
| predictions.jsonl | One record per question/method, selected source IDs, energies/coefficient arrays, solver status/bounds, exact prompt, generated answer, tokens, metrics or error |
| summary.json | Per-method answer averages including failures, failure counts, successful-only evidence/token/generation summaries |
| failure.json | Traceback for startup or interrupted-run failure, when applicable |

Results are ignored by Git because they may be large. Keep important result directories or archive them separately. A source hash identifies the code but is not a source archive: retain the corresponding checkout/diff when sharing runs. The published smoke notes are small tracked documentation.

**Experimental controls and interpretation**

Both selectors receive the same MiniLM scores and the same full candidate text. The objective minimizes negative relevance plus positive-similarity redundancy, with alpha=1 and beta=0.2 in the example configuration. These settings are inherited starting values, not newly tuned or established optimal values.

MILP solves the exact-count problem through binary x variables and continuous y variables constrained to equal each pair product. Exhaustive enumeration checks small signed-coefficient instances in tests. MILP status and bounds determine whether a solution is certified optimal; a time-limited feasible solution may still be used and is labeled accordingly.

The ranking baseline maximizes individual relevance rather than the full relevance–redundancy objective. Its selections are additionally evaluated using that same full objective for comparison. Neither solver receives gold labels. Gold supporting titles and reference answers enter only the evaluator.

The example requests exactly five documents. If fewer candidates exist, `short_pool_policy="use_all"` explicitly applies exactly min(5, candidate count) to both methods; `"error"` instead records the case as an error. Context follows original candidate order for both methods. The generator, prompt policy, tokenizer and decoding settings are common.

The sample does not enforce equal tokens, so report actual lengths and avoid attributing a quality difference solely to selection. Generation uses chat formatting and reserves output space. Context exceeding the configured total token limit fails visibly; it is not silently trimmed.

Embedding inputs exceeding MiniLM's actual maximum fail by default. An explicit `embedding_truncation="report"` mode is available for legacy-style diagnostics and records affected inputs (position zero is the question). It is not a substitute for the planned chunking implementation. Until chunking exists, larger datasets may produce recorded overlength failures.

Models load once per invocation; features are computed once per question and shared across its selectors. There is no persistent embedding cache. Preparation time, shared feature time, solver time and per-method generation time are recorded separately. Do not sum duplicated shared-feature fields to estimate actual wall time; use the invocation wall time in the manifest. Generation is actually repeated for each method, even if selections coincide.

**Metric definitions and data quality**

Answer EM/F1 follow [HotpotQA's reference rules](https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py), including punctuation/article normalization, repeated-token counts and special yes/no/noanswer handling. Empty-normalized answer pairs have EM=1 and F1=0 under those rules. Semantic synonyms can still receive zero token overlap; preserve this metric and supplement it with documented error analysis rather than silently altering it.

Document recall and complete-support coverage use annotated document titles. They are not sentence-level supporting-fact F1 or proof that the model used those sources. Missing supporting annotations produce null document metrics. All-question answer averages assign zero to failed method/question records; evidence and token summaries are successful-only and labeled as such. A nonzero CLI exit status flags recorded errors.

The first three development examples are already inspected and must not become a supposedly untouched evaluation set. Keep reference anomalies unchanged in the primary run and document them; any corrected-label analysis must be separate and justified independently of which method wins.

**Teaching exercise**

The MILP linearization uses 0 <= y <= 1, y <= x_i, y <= x_j, and y >= x_i + x_j - 1 for binary x. Work out y for (x_i,x_j)=(0,1) and (1,1). Explain why y need not be declared integer. The learning log records the answer only after the learner supplies it.
