# Quantum RAG research progress and mathematical formulation

**Version 0.4 | Updated November 10 2026**

Current execution updates follow the historical baseline account. Phase A now has a measured GPU environment, research protocol and literature matrix; phases B–I are in progress or pending. The status table below describes the pre-run baseline.

The current implementation establishes a controlled classical baseline for context selection in retrieval augmented generation. Relevance ranking and a constrained mixed integer linear program (MILP) select from the same candidates, generate actual answers and record answer quality separately from evidence coverage and objective values.

The first run completed six method–question executions on three development questions. Both methods selected five passages and achieved answer EM/token F1 of 0.3333. MILP achieved lower objective values on all three instances. This execution check establishes neither general answer superiority nor quantum advantage.

## Research objective

The proposed study asks whether question-specific evidence relationships can guide sparsification of the context-selection objective while preserving multi-hop answer quality and reducing compiled QAOA resource costs.

A passage can be topically relevant without supplying a needed fact. Complementary passages may jointly answer a question. The proposed graph model would distinguish these relationships from repeated information.

The contribution remains conditional on the literature review and experiments. Prior work covers QUBO evidence selection, passage set selection, graph retrieval and QAOA sparsification [1–4]. Combining those ideas alone does not establish novelty.

## Implementation status

The implemented flow is supplied candidates → shared MiniLM features → fixed-count ranking or MILP → consistently ordered context → Qwen generation → evaluation and artifacts. Gold annotations enter only the evaluator.

| Phase | Current status | Implemented scope and remaining work |
| --- | --- | --- |
| A reproducibility and protocol | Partial | Package, config, manifests, tests and CI workflow exist; full dependency locking, profiling and literature matrix remain |
| B data and answer evaluation | Partial | Label isolation, answer/document metrics and real generation exist; fresh frozen splits, sentence mappings and diagnostics remain |
| C retrieval and caching | Started | Fixed-count controls exist; chunking, persistent cache/index, retrieval baselines and token-budget mode remain |
| D optimization and evidence modeling | Partial | MILP, linearization and exhaustive checks exist; other baselines, token constraints and graph features remain |
| E QAOA and resources | Legacy wrapper only | Integrated experiments, mapping checks and full circuit accounting remain |
| F sparsification method | Planned | Method, generic comparisons and ablations remain |
| G frozen evaluation | Planned | Multi-dataset runs, additional generator and uncertainty analysis remain |
| H manuscript and demonstration | Planned | Progress documentation exists; full manuscript and demonstration remain |
| I submission package | Planned | Reviewed manuscript and reproducible release remain |

No complete formal phase A–I is claimed. The first working baseline spans parts of several phases. Earlier exploratory document-recall comparisons used classical optimization and unequal selection sizes; their figures are not directly comparable to the controlled answer evaluation below.

## Implemented mathematical formulation

For normalized question and passage embeddings u and vᵢ, define relevance and nonnegative redundancy:

$$
r_i=u^\top v_i,\qquad S_{ij}=\max(v_i^\top v_j,0).
$$

The current count-constrained selection model minimizes:

$$
E(x)=-\alpha\sum_i r_i x_i+\beta\sum_{i<j}S_{ij}x_ix_j,
\qquad \sum_i x_i=k,\quad x_i\in\{0,1\}.
$$

Each passage pair is counted once. The negative term rewards relevance; the positive term penalizes similar selected passages. These scores are proxies for useful evidence, not answer probabilities.

MILP replaces each product by a continuous auxiliary variable and imposes:

$$
0\le y_{ij}\le1,\quad y_{ij}\le x_i,\quad y_{ij}\le x_j,\quad
y_{ij}\ge x_i+x_j-1.
$$

With binary x, these inequalities enforce yᵢⱼ = xᵢxⱼ exactly. SciPy/HiGHS solves the resulting linear formulation with the native count constraint [5]. Status, bounds and feasibility distinguish certified optima from limited executions.

Ranking maximizes individual relevance under the same count budget; its selection is additionally scored under the full energy. It is a policy baseline, while a future MILP–QAOA solver comparison must keep the full objective and feasible set fixed.

The proposed graph extension would add a complementarity reward. Token-budget constraints and quantum encodings are not part of the measured run. The legacy QAOA wrapper simulates quantum states; no integrated quantum or hardware result is reported.

## Evaluation and experimental controls

Answer exact match compares normalized strings. Token F1 uses multiset overlap with HotpotQA's normalization and special-answer rules [7]. Document recall measures the fraction of annotated supporting titles selected; complete support records whether all such titles are present. These document metrics are not sentence-level supporting-fact F1.

The common model revisions, candidate pools, ordering and prompt policy control several variables. Exactly five selected passages controls count, but not token length. Failed executions remain in answer denominators; evidence and token summaries are successful-only and labeled accordingly.

## Verified development experiment

The experiment ran on November 4. Its saved predictions, coefficients, references and hashes were audited on November 9. No new model inference was performed during documentation updates.

<!-- BEGIN VERIFIED BASELINE RESULTS -->

Run identifier: baseline_dev_001. The input is the first three already inspected questions in the processed development set, drawn from HotpotQA's training partition. The same candidates, normalized embeddings, ordering policy and generator settings were used for both methods. These examples are not an untouched evaluation set.

| Setting | Recorded value |
| --- | --- |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Generator | Qwen/Qwen2.5-1.5B-Instruct |
| Selection budget | Exactly five passages per method on each example |
| Weights and seed | α = 1.0, β = 0.2, seed = 42 |
| Execution | CPU float32, four PyTorch threads |
| Generation | Deterministic decoding, at most 32 new tokens |
| Input policy | 4,096-token total limit with output space reserved |
| MILP limit | 10 seconds per selection, zero requested relative gap |
| Model preparation | 4.72 seconds |
| Recorded invocation wall time | 61.32 seconds |

The model revisions and runtime versions are preserved in the evidence snapshot. Models loaded from local snapshots; document embeddings were recomputed once per question and shared between selectors. A persistent embedding cache is not implemented.

| Measurement over three questions | Relevance top k | MILP |
| --- | ---: | ---: |
| Successful executions | 3 of 3 | 3 of 3 |
| Mean passages selected | 5.00 | 5.00 |
| Answer exact match | 0.3333 | 0.3333 |
| Answer token F1 | 0.3333 | 0.3333 |
| Supporting-document recall | 0.6667 | 0.8333 |
| Complete supporting-document coverage | 0.3333 | 0.6667 |
| Mean context tokens | 615.33 | 710.00 |
| Mean generation time in seconds | 8.54 | 9.15 |

No embedding truncation or generated-output-limit hit occurred. All three MILP selections reported optimal status for the specified count-constrained objective.

| Example | Ranking energy | MILP energy |
| --- | ---: | ---: |
| Q1 body double | −1.317200 | −1.842702 |
| Q2 literary movement | −1.657102 | −1.749583 |
| Q3 film | −1.663005 | −1.727368 |

All energies use the same full objective for each question. Lower values are better under that objective. They are not answer probabilities or evidence of a quantum improvement.

| Example | Reference | Ranking answer | MILP answer | Token F1 for both |
| --- | --- | --- | --- | ---: |
| Q1 body double | Rosie Mac | Rosie Mac | Rosie Mac | 1.0 |
| Q2 literary movement | Romantic | Romanticism | Modernismo | 0.0 |
| Q3 film | Richard E. Grant | Jack and Sarah | Jack and Sarah | 0.0 |

Q1 corresponds to 5abed9f45542994516f4545a, Q2 to 5ab1dd6c5542993be8fa9860 and Q3 to 5adfa059554299025d62a2f8.

<!-- END VERIFIED BASELINE RESULTS -->

## Interpretation and limitations

MILP improved objective values and annotated document recall on this sample without improving aggregate answer EM/F1. Its contexts were longer in tokens despite identical passage counts. A token-budget comparison is needed to isolate that difference.

Q2 illustrates metric sensitivity: Romanticism and Romantic have no exact normalized token overlap. MILP's Modernismo prediction is a separate error requiring evidence inspection. Q3 asks for a film but has a person as its reference; the November 4 investigation found the same inconsistency in the cached upstream record. The original primary reference is retained.

Three inspected development questions, one seed and one generator cannot establish significance or general superiority. No corpus-scale benefit, novel graph result or quantum advantage has been demonstrated.

## Correctness and reproducibility

Seventeen offline test methods passed again on November 9, covering label isolation, metric edge cases, signed-pair optimization, count boundaries, MILP/exhaustive agreement, solver limits, configuration and resume/failure behavior. The CI workflow exists; a completed remote CI run is not claimed.

The manifest records model revisions, configuration, question IDs, runtime/device and source/data hashes. Question-level records retain prompts, predictions, selections, coefficients, metrics and status. Saved energies and metrics were independently recomputed, aggregates checked and recorded source/data hashes verified.

Full local artifacts are in results/baseline_dev_001. A [compact evidence snapshot](research_report/evidence/baseline_dev_001.json) preserves configuration, artifact hashes and six outcomes. Hashes identify an execution state but do not archive the source, dataset or complete software environment.

## Planned work

Immediate work includes the structured prior-work comparison, data provenance and frozen splits, token-aware chunking, persistent embeddings and token-budget selection. Further classical baselines will precede graph-feature and QAOA comparisons.

The quantum study will account for mapping, constraints, state preparation, mixers, compilation and noise. Cardinality penalties can introduce all-pairs couplings, so a sparse semantic graph alone cannot establish circuit savings. Full and sparse objective values will be reported separately.

The final evaluation targets an additional multi-hop dataset and generator, fresh examples, multiple seeds, ablations, corpus retrieval and paired uncertainty estimates. An API and evidence-inspection demonstration will reuse the research library.

Detailed derivations and worked examples are in [Technical foundations and implementation notes](TECHNICAL_FOUNDATIONS.md). The [development sequence](DEVELOPMENT_SEQUENCE.md) records component dependencies, decisions and phase status.

## References and implementation pointers

1. Singh and Vadlamani. [QUBO Optimized Evidence Selection for Retrieval Augmented Question Answering with Unconventional Solvers](https://arxiv.org/abs/2607.12334). 2026 preprint; a direct formulation-overlap lead for the literature review.
2. Lee and colleagues. [Shifting from Ranking to Set Selection for Retrieval Augmented Generation](https://aclanthology.org/2025.acl-long.861/). ACL 2025.
3. Melo and colleagues. [Do Not Forget the Base Retriever](https://aclanthology.org/2025.emnlp-industry.174/). EMNLP Industry 2025.
4. Moondra and colleagues. [Promise of Graph Sparsification and Decomposition for Noise Reduction in QAOA](https://arxiv.org/abs/2406.14330). Relevant sparsification research; not evidence for the proposed RAG method.
5. SciPy. [MILP interface and solver status documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).
6. IBM Quantum. [Quantum approximate optimization algorithm](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm).
7. HotpotQA. [Official answer and supporting-fact evaluator](https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py).

Current implementation pointers: [data boundaries](../src/qrag/data.py), [objective and MILP](../src/qrag/optimization.py), [model adapters](../src/qrag/models.py), [metrics](../src/qrag/metrics.py), [runner](../src/qrag/experiments/run.py), [artifacts](../src/qrag/experiments/artifacts.py), [configuration](../configs/dev_baselines.toml), [tests](../tests/test_baselines.py) and [legacy QAOA wrapper](../src/optimization/qaoa_solver.py).

## Phase A — measured environment and research protocol (November 10, 2026)

The execution environment now exposes CUDA. The measured RTX 5060 has approximately 7.53 GiB of PyTorch-visible device memory; the host provides 16 logical CPUs. The earlier CPU-only experiment remains unchanged. GPU tensor multiplication, a two-qubit Bell-state simulation and a HiGHS binary optimization were executed, rather than inferring compatibility from installed versions. The baseline's 17 offline tests pass and pip reports no broken requirements.

The [environment evidence](research_report/evidence/environment_20261110.json), [host-specific dependency snapshot](../requirements-laptop.lock), [research protocol](EXPERIMENT_PROTOCOL.md) and [19-source literature matrix](LITERATURE_REVIEW.md) establish the execution foundation. The lock records installed transitive dependencies for this Linux/Python/CUDA host; it is not a universal GPU installation recipe.

The contribution shortlist is evidence-guided interaction removal and its dependence on constraint encoding. Prior work already covers QUBO evidence selection and QAOA sparsification. An exact reproduction of the closest paper has not been achieved: its requirement estimators and original model configuration are different. A transparently labeled local adaptation is planned. No new answer-quality improvement or quantum advantage is claimed in this phase.

Historical schedules are superseded by a quality-first execution order. The study will use laptop compute, frozen held-out IDs, paired comparisons and explicit simulation labels. Full literature novelty certification, external review and publication acceptance are not software acceptance criteria.

## Phase B — data boundaries, frozen splits and scorer verification

The new adapters preserve original HotpotQA sentences and supporting sentence indices. MuSiQue keeps paragraph identities separately from titles, because distinct paragraphs can share a title. Answer aliases and supporting annotations remain in evaluation-only objects. Invalid mappings fail validation.

The [split manifest](../configs/splits/research_v1.json) freezes 100 development and 500 held-out questions per dataset, before model evaluation on the held-out data. Earlier local HotpotQA IDs and normalized questions were excluded. The new held-out material comes from official validation/dev partitions, not a hidden test set. Normalized exact matching and token-trigram Jaccard at 0.8 found no near matches between the selected new development questions and the evaluation candidate samples. This limited audit cannot rule out paraphrases, shared facts or model pretraining contamination. No structural rejection was needed in the sampled preparation pass.

HotpotQA retains 228 supporting sentence annotations across the development sample and 1,223 across evaluation. MuSiQue has paragraph support, not sentence support; its 100 development questions include 44 answer aliases and its 500 evaluation questions include 199. Raw data remain outside Git. Sources, licenses, immutable HotpotQA revision, official MuSiQue archive hash, IDs and file hashes are recorded in the manifest.

The [metric audit](research_report/evidence/metric_verification.json) compares 1,004 deterministic answer pairs per dataset against inspected official evaluator functions: every EM and F1 agrees. The offline suite now has 21 passing tests. A six-generation GPU diagnostic uses three development questions with empty or gold-evidence context; its [records](research_report/evidence/phase_b_diagnostics.json) preserve answers, token counts and metrics. These diagnostic contexts have different sizes and are not a fair selector comparison. Neither the diagnostic nor metric verification establishes a method improvement.

Generation now records input token IDs and explicitly records its numeric precision. The new float16 GPU execution is a separate condition from the original float32 CPU experiment. No weights are trained or changed.

## Phase C — token-safe retrieval, cache and persistent index

Implemented sentence-aware chunks with original character ranges and sentence IDs. Long sentences are split into overlapping token windows; ordinary sentence boundaries are preserved. Embedding input includes a bounded title prefix and is checked against the model limit. All chunks contribute to a document representation through mean pooling followed by unit normalization. This explicitly changes the earlier truncated-passage representation; its benchmark outcomes must not be merged with the historical baseline.

Added a SQLite content-addressed embedding cache, separate query/document namespaces, checksums, model/policy identity, an exact FAISS inner-product index with SQLite metadata, BM25, reciprocal-rank fusion and a revision-pinned cross-encoder with maximum-over-chunks aggregation. Index loading verifies both vector and metadata checksums. These are reusable library components; installing them alone is not an end-to-end corpus benchmark.

In a [50-question development profile](research_report/evidence/retrieval_profile.json), the first encoding pass had 584 misses and no hits and took 1.587 seconds with the model already loaded. The repeated pass had 584 hits, no misses and took 0.296 seconds. These are feature-stage measurements, not end-to-end RAG latency. The 534-chunk index returned identical results after restoration. All 25 offline tests pass, including long-sentence text coverage, changed cache identity, corrupt cache entries and index corruption.

Fixed-count and generator-token-budget selection will be integrated with the native solver constraints in Phase D. A restored index and a cache speedup do not establish answer-quality improvement. The cross-encoder is downloaded and implemented; its real comparative results are deferred to controlled evaluation.

## Phase D — constrained selectors and transparent evidence features

Implemented native token-budget constraints alongside exact-count constraints. MILP uses the same signed pair objective and continuous product variables in both modes. Added MMR, greedy energy descent, greedy lexical coverage, and seeded simulated annealing with feasible swaps/additions/deletions. BM25, hybrid and cross-encoder rankings select through the same budget validator. All methods receive the same candidate text and generator settings.

The evidence representation is explicitly an entity-link graph, not a verified factual knowledge graph. Candidate-title mentions and capitalized spans retain exact source offsets. A question-term anchor score and positive dense relevance weight linked passage pairs. Shared names are weak indicators of possible bridges, not proof of complementary facts. Extraction artifacts are cached by inference content and extractor revision, with payload checksums. Typed relation extraction is not justified by the current negative pilot and remains a conditional extension.

The [50-question fixed-count pilot](research_report/evidence/phase_d_development.json) contains 500 successful method/question records. Mean answer F1: top-k 0.6123; BM25 0.6370; hybrid 0.5897; reranker 0.5780; MMR 0.5631; greedy coverage 0.6409; base MILP and annealing 0.5818; graph MILP with gamma=0.8 0.5455. Every method selects five passages, but token lengths differ. These development estimates do not establish a statistically supported ranking. The negative graph result is retained and motivates checking feature alignment rather than claiming improvement.

The separate [900-token development pilot](research_report/evidence/phase_d_tokens.json) contains 100 successful records on 10 questions. Every actual assembled context is within the cap. Base MILP mean F1 is 0.475 and top-k is 0.675; coverage is 0.755. Mean selected counts differ because this is a token-budget experiment. It must not be pooled with the fixed-count pilot.

Twenty-nine offline tests pass. MILP matches exhaustive optima on signed-pair token-budget cases; infeasible minimum-count cases return no solution. The study runner preserves exact source snapshots, coefficients, graph provenance, prompts, token IDs and per-method failures. Identical selections reuse deterministic generation within a question, with explicit reuse and actual-execution timing fields. The exported compact evidence preserves outcomes without redistributing full passage prompts.

An independent annotated entity-resolution audit and exact original-model prior-work reproduction are not completed. Neither graph labels nor gold reference fields enter the normal graph/solver/generator path.

## Phase E — actual QAOA, feasibility and circuit resources

Implemented and executed Qiskit QAOA using the same fixed-count selection instances as MILP. Exact statevector expectation optimization is distinguished from final finite-shot measurements. A separate method uses 256 training shots per objective evaluation. No quantum hardware, hardware speedup or noisy parameter optimization is claimed.

The implementation verifies the QUBO/Ising spectrum and little-endian bit mapping, uses a sufficient cardinality-penalty strength or a count-preserving XY mixer, records every optimizer evaluation, and selects the lowest surrogate-energy feasible measured sample without repair. It compiles the complete circuit, including initialization and mixer, to rz/sx/x/cx on explicitly synthetic all-to-all and line targets. The line is not a calibrated device.

The [10-question development experiment](research_report/evidence/phase_e_qaoa.json) contains 140 successful records: MILP, both mixers at p=1/2 and three seeds, plus finite-shot training. Mean answer F1 across the balanced three-seed groups: XY p=1 0.4167; XY p=2 0.4617; penalty p=1 0.4417; penalty p=2 0.4750. MILP is 0.4750. These small development figures support execution and diagnostics, not superiority claims.

Ideal XY final shots are all feasible. Mean penalty feasible fractions are 0.3622 at p=1 and 0.5270 at p=2. Mean compiled line two-qubit gates are 261.03/546.07 for XY p=1/2 and 199.33/396.67 for penalty p=1/2. Thus preserving count did not make this dense circuit cheaper. Resource distributions and paired uncertainty belong to final evaluation.

A separate [three-question, eight-candidate diagnostic](research_report/evidence/phase_e_noise.json) applies synthetic depolarizing noise only during final sampling. Ideal XY feasibility is 1; noisy feasible fractions are 0.6494, 0.6641 and 0.6270. Angles are still trained ideally. These are simulation results with an artificial noise model, not physical-device estimates. Quantum token-budget encoding remains conditional and is not implemented; token-budget comparisons currently use classical selectors.

The offline suite now has 32 passing tests. The laptop statevector study is explicitly capped at 16 candidates, avoiding any suggestion that these simulations establish large-scale quantum performance.

## Phase F — calibrated weights, sparsification and research decision

A development-only sweep used 100 questions per dataset and gamma in {0,0.1,0.2,0.4,0.8}. Gamma=0.2 maximized the unweighted mean answer F1 across the two development datasets; the decision and all scores are [recorded](../configs/development_decision.json). HotpotQA base/selected-weight F1 is 0.6358/0.6533; MuSiQue is 0.1868/0.2205. These are tuned development results, not held-out gains. Greedy lexical coverage remains a strong comparator. The earlier gamma=0.8 negative result is not removed.

Implemented exact unordered-edge budgets for absolute magnitude, seeded random, endpoint-degree ranking and evidence-guided protection. Evidence guidance reserves at most half the hard edge budget for high-priority possible bridges and fills the rest by coefficient magnitude. It never silently exceeds the budget, even if more links are candidates for protection. Retained coefficients keep their signs. Every solution is scored under both its sparse surrogate and the original full objective.

The [30-question development ablation](research_report/evidence/phase_f_sparsification.json) contains 900 successful records. Full graph MILP mean F1 is 0.6203; full XY-QAOA is 0.5634; uniform best-of-1,024 feasible samples is 0.6203. At half edges, QAOA absolute and evidence-guided selection both score 0.4834; the corresponding sparse MILPs score 0.4491 and 0.4891. Small-sample/tuning limitations prevent a general ranking claim.

Mean line two-qubit gates fall from 263.87 for full XY-QAOA to 176.43 for absolute and 176.63 for evidence-guided half-edge variants. The half-edge penalty variants both have 45 encoded pairs and 199 mean line gates. Thus edge removal does reduce complete compiled cost in one encoding while the penalty can erase structural savings. It does not establish preserved answer quality.

Research decision: continue as an encoding-aware comparative study rather than promise a positive evidence-preservation result. The [analysis](research_report/evidence/phase_f_analysis.json) retains paired uncertainty. Add uniform feasible sampling to final comparisons because best-of-many measurements can cover much of a small feasible space. No quantum advantage is inferred from finding a good subset after many classical energy evaluations.

The study runner now uses an append/fsync journal with explicit error retries and torn-tail recovery. Successful records cannot be overwritten; a changed resume identity fails before file mutation. Report generation groups repeated solver seeds within question before resampling. Thirty-eight offline tests pass. A reconstruction check rebuilt all four frozen dataset files in a separate directory and matched their exact hashes.

## Phase G preparation — frozen evaluation matrix

Before new held-out execution, froze [18 configurations](../configs/final_matrix.json) specifying 50,290 method/question evaluations. The main classical comparison uses 500 questions per dataset with Qwen 1.5B and Qwen 3B. Token studies use the first 100 frozen IDs per dataset/generator. The principal quantum comparison uses 50 frozen IDs per dataset, a common label-independent top-10 pool, and three solver seeds. Larger MuSiQue quantum sensitivities use five questions at 12/16 real candidates. Bounded corpus studies use 25/50/100 candidates with separately stated sample sizes and one-second MILP limits.

The bounded corpora contain 5,941 HotpotQA documents/6,270 chunks and 8,582 MuSiQue documents/8,972 chunks, deduplicated by title plus text from permitted benchmark input passages. They are not full Wikipedia. Candidate retrieval uses only the question and corpus; supporting labels are mapped afterward for evaluation, including retrieval misses.

Qwen 3B completed a development generation using approximately 6.49 billion peak allocated GPU bytes. One 16-candidate development QAOA profile took 1.05 seconds. These are smoke/profile checks, not general resource or accuracy conclusions. Thirty-nine offline tests and the configured lint checks pass. The evaluation results are not yet complete at this preparation checkpoint.

## Phase G implementation erratum before the definitive run

The first execution cycle exposed a provenance assertion bug on “İstanbul High School”: Unicode-aware case-insensitive regex matching does not imply equality of the two case-folded strings. One HotpotQA question failed in the first count run for all 19 methods. The matrix was stopped, all started run artifacts were retained under a separate archive, and the source-span check was repaired to store the actual surface text separately from the canonical entity name. A Unicode regression test now verifies exact source offsets. The graph-cache revision was incremented.

All 18 conditions will be restarted under the repaired code. Models, IDs, budgets, gamma, selectors, sparsifiers and analysis decisions are unchanged. This is an implementation repair, not a new development search using held-out answer scores. The [erratum evidence](research_report/evidence/evaluation_cycle1_erratum.json) identifies the superseded runs; those outcomes are excluded from definitive comparisons. SQLite connections are also now explicitly closed after graph/index transactions, without changing their numerical definitions. Forty-five offline tests pass.

## Phase H preparation — service and manuscript source

A separate service package now calls the common frozen research library. It provides strict input schemas, a one-worker bounded inference queue, SQLite job persistence, readiness/health endpoints, explicit quantum-to-classical fallback, persistent corpus ingestion/query endpoints and structured stage traces. A dashboard exposes source selection, generated answers, token use and simulation costs. It does not treat supplied sources as verified citations or claim that prompt wording prevents injection.

The full CPU container builds successfully from a pinned Python image and resolves both immutable local model snapshots through a read-only model-cache mount. HTTP checks verify the dashboard, health and truthful cold readiness responses. Forty-five local tests pass, including validation, queue-full behavior, failure recording, restart handling and explicit fallback. Real-model HTTP benchmarking is scheduled after the research jobs to avoid competing for model memory. No enabled browser is available for visual dashboard review.

An editable manuscript source and a ReportLab PDF renderer are prepared. Final results and conclusions remain unfilled until the definitive matrix and separately declared controls complete. The secondary controls add a common complete-compiled-gate cap and base-versus-graph QAOA comparison without changing the 18 primary configurations.
