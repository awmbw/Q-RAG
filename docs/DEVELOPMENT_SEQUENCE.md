# Development sequence and implementation decisions

**Version 0.1 | Updated November 9 2026**

This document records the progression from the exploratory prototype to the first controlled baseline. The baseline was implemented during one November 4 session. Its steps below are arranged by dependency and explain how the components fit together; they are not presented as separate commits or separately timestamped releases.

The [progress report](RESEARCH_PROGRESS_REPORT.md) records outcomes. [Technical foundations](TECHNICAL_FOUNDATIONS.md) supplies derivations and worked examples.

## Starting point before the baseline

The prototype already had processed HotpotQA subsets, MiniLM retrieval, a relevance–redundancy QUBO, classical exact optimization, a local generator and a QAOA wrapper.

Its principal evaluation used the classical solver and measured selected-document quality. It did not evaluate generated answers. Its unconstrained optimizer could select more documents than top-five ranking, so higher recall could not establish a better selection policy at equal context size.

The objective was retained as a starting model, while the evaluation and execution contracts were rebuilt.

## Stage one explicit data and configuration contracts

**Added:** [data.py](../src/qrag/data.py), [config.py](../src/qrag/config.py), [configuration](../configs/dev_baselines.toml), and package metadata.

The source JSON is adapted into separate QueryInput and EvaluationLabels objects. IDs, titles, text and questions are validated; gold fields do not reach the normal inference interface. Configuration makes weights, seed, model revisions, limits and short-pool behavior explicit.

**Why this came first:** every later comparison depends on knowing its inputs and settings. A selector that can inspect reference labels or inherit hidden script constants cannot support a reliable experiment.

**Remaining:** source-sentence offsets, full duplicate checks and frozen fresh evaluation partitions. The dependency lock currently covers only the core numeric pair rather than the complete model stack.

## Stage two answer and evidence metrics

**Added:** [metrics.py](../src/qrag/metrics.py).

Answer exact match and token F1 are calculated separately from document precision, recall and complete-support coverage. Reference-normalization fixtures include repeated words, punctuation and special answers.

**Why:** document selection is an intermediate task. The project needs generated-answer measurements before claiming that a selection improvement benefits RAG.

**Verification:** offline metric fixtures and the later real generation run. Semantic near-matches and annotation inconsistencies remain visible in error analysis.

## Stage three a common objective and controlled classical selection

**Added:** [optimization.py](../src/qrag/optimization.py).

SelectionProblem stores one linear vector and a strict upper-triangular interaction matrix. An exact-count constraint prevents the optimizer from improving recall merely by choosing more passages.

The module implements stable relevance top-k, MILP with product linearization, and a tiny exhaustive oracle. SelectionResult distinguishes ranking, optimal and limited outcomes and retains bounds when available.

**Why:** formulation and solver effects must be separable. A tested energy evaluator also gives the future quantum mapping a reference independent of circuit software.

**Verification:** MILP agrees with exhaustive enumeration on tiny positive/negative-pair cases and count boundaries. Tests also cover time-limited solutions without falsely labeling them optimal.

**Remaining:** native token constraints and additional classical baselines.

## Stage four common real-model adapters

**Added:** [models.py](../src/qrag/models.py).

The model adapter resolves immutable MiniLM/Qwen snapshots, loads once, produces shared per-question features, constructs a consistent chat prompt and generates actual short answers. Embedding overlength and generation-prompt overflow fail explicitly by default.

**Why:** the compared selectors must use the same models and prompt policy. Model loading, feature generation and answer generation are distinct timing stages.

**Remaining:** chunking, persistent embedding reuse, hardware profiling and generation diagnostics with empty or oracle evidence.

## Stage five experiment orchestration and artifact integrity

**Added:** [runner](../src/qrag/experiments/run.py) and [artifact handling](../src/qrag/experiments/artifacts.py).

Each question is scored once; both methods consume the same candidate pool and features. Selected context uses original candidate order. Labels are applied only after selection/generation.

The runner saves manifests, question-level JSONL records and summaries. The manifest identifies data bytes, qrag source files, models, settings and runtime. Atomic writes and guarded resume prevent partial files and accidental mixing of incompatible runs.

**Why:** an aggregate result without the predictions and settings behind it cannot explain what changed or support a reproducibility check.

**Boundary:** completed error records are retained and skipped on resume. Failures before the run store exists may have only a CLI error; not every possible startup failure produces a manifest.

## Stage six independent correctness and package checks

**Added:** [offline tests](../tests/test_baselines.py), an editable package and [CI configuration](../.github/workflows/baselines.yml).

The seventeen test methods exercise contracts and mathematics without downloading language models. An explicitly labeled fake backend tests orchestration; it is unavailable as an experimental CLI mode.

The package installed locally without downloads. A configured CI workflow is not evidence of a completed remote CI run.

**Why:** a real model can produce plausible answers while masking a wrong objective or metric. Mathematical and interface checks need independent expected outcomes.

## Stage seven the real development run

**Experiment date:** November 4 2026. **Run:** baseline_dev_001.

MiniLM and Qwen ran locally on CPU with four PyTorch threads. There were three development questions and two methods per question. All six records succeeded with exactly five selected passages and no recorded embedding truncation or output-limit hit.

Both methods obtained answer EM/F1 of 0.3333. MILP obtained lower energy on each instance and higher average annotated document recall. Context-token consumption differed, so this was a fixed-count experiment rather than a token-matched comparison.

**What this established:** the complete baseline execution path works and exposes optimization, evidence and answer quality as different measurements.

**What remains unestablished:** general superiority, statistical significance, corpus-scale retrieval benefits, a novel graph method and a quantum advantage.

## Stage eight audit and objective documentation

**Documentation and audit date:** November 9 2026.

The saved objective energies and answer/evidence metrics were recomputed against the recorded coefficients and unchanged references. Dataset and qrag source hashes matched the saved run. The seventeen offline tests passed again.

One question had a semantic near-match rejected by token scoring. Another asked for a film but recorded a person as its answer; the earlier investigation located the same inconsistency in the cached upstream record. Neither primary label nor scoring rule was silently altered.

Added the objective progress report, compact evidence snapshot and detailed companion. No new model inference result is implied by this documentation work.

## Decisions and alternatives

| Decision | Reason | Consequence or limitation |
| --- | --- | --- |
| Use supplied pools first | Isolates context selection | Does not evaluate corpus search |
| Separate labels in data objects | Reduces accidental answer leakage | Still requires split and contamination checks |
| Start with exact-count budgets | Removes passage-count imbalance | Token lengths remain unequal |
| Use native MILP count constraints | Gives a strong checkable classical reference | Quantum encodings still require separate work |
| Use continuous product auxiliaries | Exact with binary original variables | The continuous relaxation allows more points |
| Keep original context ordering | Controls a generation variable | Order sensitivity remains an experimental question |
| Fail overlong inputs visibly | Avoids hidden representation loss | Chunking is required for larger runs |
| Use JSON artifacts before tracking infrastructure | Keeps individual outcomes auditable | Rich experiment dashboards remain later work |
| Preserve problematic references in primary scoring | Avoids result-driven label changes | Annotation errors must be reported separately |

## Status against the implementation plan

| Phase | Current status | Principal gap |
| --- | --- | --- |
| A reproducibility and research protocol | Partial | Literature matrix, contribution assessment, fuller profiling and full dependency lock |
| B data and answer evaluation | Partial | Fresh frozen splits, source mappings and diagnostic experiments |
| C retrieval and caching | Started | Chunking, cache, index, retrieval baselines and token-budget mode |
| D classical optimization and evidence model | Partial | Other classical selectors, token constraints and graph features |
| E QAOA integration and resources | Pending beyond legacy wrapper | Shared-problem quantum experiments and full cost accounting |
| F candidate sparsification method | Pending | Method, generic comparisons and development ablations |
| G frozen evaluation | Pending | Multi-dataset controlled runs and uncertainty analysis |
| H manuscript and demonstration | Pending beyond progress documentation | Complete paper, research figures and demonstration |
| I submission package | Pending | Reviewed manuscript and reproducible release |

No complete formal phase A–I is claimed merely because the first working baseline exists.

## Next dependency sequence

1. Complete the structured prior-work comparison and make the novelty hypothesis explicit.
2. Finalize data provenance, frozen splits and diagnostic evaluation.
3. Add token-aware chunking, source mappings and persistent embedding caching.
4. Implement token-budget selection and additional classical comparisons.
5. Add graph-derived features and evaluate their contribution classically.
6. Integrate QAOA with the same problems, constraints and resource reporting.
7. Evaluate the candidate sparsifier before freezing final experiments.

The [implementation plan](IMPLEMENTATION_PLAN.md) contains the full backlog. Updating this sequence should record what actually changed, why it changed and which artifact verifies it, rather than marking work complete because a planned date has passed.

## November 10, 2026 — Phase A execution foundation

1. Re-read the plan and current inference, solver and artifact contracts. The working tree was clean at execution start.
2. Verified the now-visible GPU, executed tensor/HiGHS/quantum checks, and preserved the earlier CPU experiment as historical evidence.
3. Installed the missing testing/service tools in the project virtual environment and recorded the exact installed dependency graph. No system Python or driver change was made.
4. Checked 19 primary research sources, distinguishing close-method inspection from abstract-level context. Recorded reproduction limits instead of claiming to have reproduced unavailable original settings.
5. Froze a protocol separating graph, sparsification and solver questions. Actual sample sizes will be chosen from development timing before held-out evaluation.

Verification: 17 baseline tests passed; dependency consistency check passed. New evidence: environment report. This phase establishes the research/execution foundation; it does not finish data preparation or demonstrate an empirical method benefit. Next dependency: trustworthy dataset partitions and annotation-preserving data contracts.

## November 10, 2026 — Phase B data and evaluation

Extended the existing immutable data contracts without passing labels into inference. Added official-format HotpotQA and MuSiQue-Ans adapters, sentence validation, paragraph identities, aliases and dataset-specific answer scoring. Prepared fresh frozen splits from primary sources before any new held-out model run. Downloaded only public data/model artifacts; no paid compute was used.

Verified the scoring implementation against 1,004 pairs per official evaluator, plus four new data-contract tests. All 21 offline tests pass. Executed six real GPU generations to establish empty/gold diagnostic paths and preservation of actual prompt IDs. The diagnostic is separate from the main benchmark and is not a claim of equal-budget quality improvement.

The split preparation script refuses to overwrite existing frozen output. Its source revisions, IDs and hashes enable later reconstruction. Remaining independence limits include paraphrases, common source documents and unknown model pretraining data. Next dependency: token-safe representations, persistent caches, retrieval and explicit budget handling.

## November 10, 2026 — Phase C retrieval foundation

Implemented token-aware source-preserving chunks first, then reused their exact text in the cache, dense scoring, index and reranker. This order prevents caching a silently truncated representation. Added immutable FAISS/SQLite bundles, lexical scores and rank fusion. The cross-encoder's paired input length is checked with its own tokenizer, because another model's safe input is not automatically safe for it.

The first real profile encoded 534 chunks plus 50 questions: 584 misses, followed by 584 hits on repetition. Encoding time fell from 1.587 to 0.296 seconds under this measured condition. Index restoration returned identical results. Twenty-five offline tests pass. Two initial retrieval-test expectations were corrected before this milestone: reciprocal-rank fusion is nonlinear in rank, and an intentionally tiny test chunk needed an appropriately small overlap.

No answer-quality conclusion follows from this profile. Native token constraints and comparable generated-answer runs remain coupled to Phase D's solver work. Full corpus evaluation comes later after the common candidate construction is frozen.

## November 10, 2026 — Phase D optimization and first broad pilot

Extended the common problem with optional linear token costs, a variable-count mode and minimum count. Retained the original exact-k API for historical tests. Added independent budget validation and exhaustive comparisons on small signed objectives. Added feasible heuristics before integrating graph coefficients so objective changes and solver changes remain separable.

Built the graph from permitted text and question inputs only; stored exact mention spans and named the result an entity-link graph. Added cached extraction and explicit limitations. Integrated shared candidates, token-safe embeddings, classical comparators, full source snapshots and compact exports in a new study runner while retaining the historical baseline entry point.

Executed 500 fixed-count development records (50 questions by 10 methods) and 100 token-budget records (10 by 10). All completed successfully; actual token caps were independently checked. The first graph weight worsened mean answer F1 relative to the base objective. That result is retained, and no graph improvement is claimed. Twenty-nine offline tests pass. Independent graph annotation and original-model prior reproduction remain limitations. Next dependency: exact quantum mapping, actual QAOA sampling and complete compiled-resource accounting.
