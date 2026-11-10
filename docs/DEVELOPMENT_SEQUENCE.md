# Development sequence and implementation decisions

**Version 1.0 working edition | Updated November 10 2026**

This document records the progression from the exploratory prototype through the current research implementation. The first baseline was implemented during one November 4 session; its dependency-ordered account comes first. The November 10 phase entries then record the larger data, retrieval, optimization, quantum, service and research work. Early status tables are labeled historical and do not override later measured progress.

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

## Historical status after the first baseline

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

## Dependency sequence recorded after the first baseline

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

## November 10, 2026 — Phase E integrated quantum experiments

Implemented the Ising map and exhaustive spectrum checks before QAOA. Added both dense cardinality penalties and a seeded count-preserving XY ring, then exact-expectation/finite-shot training and explicit final-sample selection. Added complete-circuit compilation on common synthetic targets and an optional final-measurement noise model.

Executed 140 records on 10 development questions with two depths, two mixers and three seeds, plus a shot-training control. Executed a separate nine-record noise diagnostic on three questions after label-independent relevance reduction to eight candidates. All records completed successfully. Thirty-two offline tests pass. Observed that ideal feasibility and compiled cost trade off: XY preserves count but is costlier for these dense instances; synthetic noise substantially reduces its measured feasibility. No hardware or speedup claim is made.

The next dependency is sparsification: retain a declared number of interactions, compare against generic rules, and always evaluate selected contexts under the original full target. Any claimed savings must survive the constraint encoding and compilation just measured.

## November 10, 2026 — Phase F development decisions and sparsification

Implemented all four hard-budget sparsifiers and checked signs, masks and the elementary full-energy bound against exhaustive optima. Added a best-of-feasible-random-samples control because the quantum policy also evaluates many measured candidates. Added paired question-level analysis and tests preventing seed repeats from becoming artificial sample size.

Ran 1,400 calibration records across 200 development questions, selecting gamma=0.2 before held-out evaluation. Ran 900 sparsification/encoding development records across 30 questions. The results support a compiler/encoding effect but not a reliable superiority claim for evidence guidance. Continued the study as a controlled comparison, retaining unfavorable outcomes and original settings.

Replaced quadratic-cost artifact rewrites for the new study runner with a durable append journal and explicit retry semantics; the legacy runner remains historically compatible. Added a restore-by-manifest script and verified all four dataset hashes after independent reconstruction. Thirty-eight offline tests pass. Next: freeze the complete evaluation matrix, run new held-out questions, quantify paired uncertainty, then write the manuscript around observed findings.

## November 10, 2026 — Phase G freeze checkpoint

Added bounded-corpus retrieval and explicit evaluation of missing support, then constructed the common candidate files before answer generation. Added memory high-water marks and stage timing fields. Formatted and linted the Python sources and reran all 39 tests before freezing the final configurations. Completed a separate Qwen 3B GPU smoke and a 16-candidate development quantum profile. The frozen matrix is now ready for execution; no held-out result is claimed at this checkpoint.

### Phase G restart: provenance invariant repair

A real held-out input revealed the Unicode surface/canonical distinction. Stopped the matrix, retained the complete first run and partial subsequent run, reproduced the assertion from the source text, added a targeted regression, and restarted every condition with unchanged scientific settings. Forty-five tests pass. The first cycle remains an auditable superseded implementation run, not a pool from which favorable results are chosen.

## Phase H parallel preparation while frozen runs execute

Placed the API in a separate package so service changes do not alter the frozen research source fingerprint. Implemented input validation, bounded jobs, persistence, readiness, fallback accounting, corpus ingestion/query and local tracing. Built and started the full CPU container, verified HTTP endpoints and checked read-only access to the pinned model snapshots. The browser inventory is empty, so visual UI review is not claimed. Prepared the manuscript source and PDF renderer, deferring numerical claims until the full results exist.

## Phase G diagnostic extension — check what a shallow circuit can express

Added an answer-free development mechanism study rather than interpreting the final best-of-1,024 sample alone. It trains 480 circuits across 20 questions and nested sizes, then computes optimum coverage and expected best feasible energy directly from each ideal distribution. The first export exposed a roughly 10^-15 negative no-feasible probability from normalization roundoff; clamped probability sums at their mathematical [0,1] boundary, retained the initial local export, and regenerated the diagnostic. No scoring coefficients or training policy changed.

The result prompted an analytic circuit check: the original first cost layer acts on a basis state and is a global phase. Confirmed this by varying the angle and comparing complete probability vectors. Added a regression showing that a fixed feasible preparation sweep makes the first cost angle observable while preserving count. This was a mathematical diagnosis, not a search for a favorable answer score.

Kept every original frozen condition. Added separately hashed, explicitly exploratory prepared-circuit configurations, with one fixed pi/4 XY ring sweep before cost evolution. Archived extension source separately and included its hash in the study identity. This avoids changing the core while original experiments are active and makes the difference reproducible. The forthcoming analysis must compare the original and prepared circuits, disclose the post-freeze scope, and include preparation costs. Forty-six correctness tests are now defined; the new mathematical regression passes.

Prepared independent final artifact audits, compressed prediction exports, restoration of all six corpus-candidate files and model-free table reconstruction. The restored corpus inputs matched their frozen hashes exactly. Circuit summaries include measured zero-feasibility failures, preventing a successful-only denominator from overstating feasibility. Final answer comparison assembly remains dependent on completion of the frozen runs.

## Phase H packaging checkpoint — keep installation evidence separate

Captured and pinned the observed CPU container dependencies rather than assuming the CUDA laptop lock was portable. Rebuilt the image, started a nonroot instance with persistent state and a read-only model mount, verified its health/readiness/dashboard responses and ran pip compatibility checking. Model-job performance is still a separate pending measurement. Documented installation, API semantics, reproduction, upstream rights and current publication routes.

The full remote research CI passed. The minimal workflow exposed that the new preparation regression lacked the optional-Qiskit skip used by the other quantum tests. Corrected that dependency boundary and retained actual execution in the full suite; all 46 local tests pass. Prepared a deterministic, unjudged 40-edge graph worksheet so external semantic review can use source-grounded examples without mistaking automated extraction for verified factual relations. No human annotation result is invented.

<!-- BEGIN COMPLETED_EVALUATION -->
## Phase G completion — frozen outputs before interpretation

Finished all 18 primary configurations without changing their settings. Retained the one zero-feasible-shot failure and all failed cap diagnostics. Finished separate formulation, gate-cap and prepared-state controls. Audited 53,230 records across 24 grids, including independent tokenization/energy checks and recompilation of the gate-capped final circuits. All primary/formulation conditions use the same core source fingerprint; the prepared extension has a separate composite identity.

Generated full method tables, paired intervals, resource plots, token/corpus sensitivities and deterministic error examples. The principal sparsification comparison does not establish the intended evidence-guidance benefit. Kept the research framing comparative and diagnostic. No post-hoc noninferiority margin, winning-seed selection, physical-hardware claim or answer-based parameter adjustment was introduced.

Exported compressed public outcomes, common source snapshots and 110 frozen coefficient instances. Reconstructed all public tables without neural inference and reproduced four actual solver cases, matching selected IDs, full energies and line compilation. These checks complement the earlier exact restoration of all split/corpus files.

## Phase H completion checks — actual execution beyond fixtures

Ran real CPU-container ingestion and five repeated three-selector comparisons. Verified cache reuse, local traces, persistent corpus retrieval and exact job-response survival after recreating the container on the same state volume. The single untrusted-source input was not selected into context, so it supplies no generator-resistance evidence. Browser visual review remains unavailable and is not represented as completed.

Profiled GPU embedding batches on 128 fixed development chunks, with three randomized repeats and synchronized timing. Verified the 240-token bound and vector agreement. Preserved the initial local timing export and published the final length-validated measurement. These operational profiles did not change scientific settings. Final manuscript export, page inspection and the versioned artifact package follow these checks.

<!-- END COMPLETED_EVALUATION -->

## Phase H manuscript export — inspect the rendered artifact

Completed the numerical manuscript and architecture/resource/sampling figures. Added explicit count/token, MILP, Ising, penalty and global-phase equations. Rendered the PDF, inspected all pages, widened method columns, kept figure captions and equation introductions with their content, and placed references on a dedicated page. Rebuilt and inspected the final 13-page export. Saved hashes and page-level QA evidence. This finishes the local manuscript/demo milestone; it does not claim external scientific approval, browser visual review or scholarly submission.

## Phase I — package the measured state and preserve the handoff

Prepared a clean-commit release builder for source/configuration/evidence, the installable wheel, reviewed PDF and SHA-256 checksums. Added a claim-to-evidence map and an explicit list of external review, authorship, licensing, annotation and submission tasks. Added model-free public-table and original/prepared quantum reproduction commands to the full CI workflow. Kept the negative findings, local source archives and primary-versus-exploratory distinction intact.

The resulting artifact is a versioned research preview. It is not labeled as a submitted, accepted or independently validated paper. The local implementation, experiments, source restoration, statistical reconstruction, service checks and PDF inspection are complete within the recorded scope. No remaining human-only decision is represented as an automated result.
