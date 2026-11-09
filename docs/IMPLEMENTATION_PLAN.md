> Execution update, November 10, 2026: all phases and post-manuscript engineering are authorized. Research quality takes priority over the historical dates below. Laptop compute only; no paid allocation or quantum hardware. Evidence-based changes of research direction are permitted. See [protocol](EXPERIMENT_PROTOCOL.md) and [literature matrix](LITERATURE_REVIEW.md).

**Q-RAG implementation plan — November 4, 2026**

This is the detailed execution plan for the publication, research software, demonstration and teaching work. It supersedes the November 1 roadmap's schedule and venue status where they differ. The proposed research method remains conditional on a literature review and development experiments. This document does not report new experimental results. The commands and module layout below describe planned interfaces, not features already implemented.

**1. Priorities and intended result**

Priority order: a defensible research contribution and manuscript; reproducible experiments; a dependable working system; recruiter-facing presentation and interview preparation. Teaching happens throughout. A useful result may establish a quality/resource tradeoff or a limitation; it need not establish practical quantum advantage. Acceptance cannot be guaranteed.

The research question is: can question-specific evidence relationships guide sparsification of the context-selection objective so that QAOA needs fewer compiled resources while preserving multi-hop answer quality better than generic sparsification?

Working title: Evidence-Preserving Sparsification for Quantum Context Selection in Multi-Hop RAG. "Evidence-preserving" expresses a hypothesis, not an established guarantee. Applying QUBO, adding a knowledge graph, and generic QAOA sparsification are already established ideas. Their combination needs a precise new result, not a new name.

Target deliverables are a manuscript, a reproducible research package, complete result manifests and analysis scripts, a small evidence-inspection demonstration, and a learning log based on the learner's actual answers. A more polished deployed service follows the main manuscript experiments.

**2. Starting point and resources**

The existing project includes MiniLM embeddings, relevance and similarity matrices, a relevance–redundancy QUBO, a Qiskit exact solver, a QAOA wrapper, a Qwen generator and development/evaluation scripts. The main evaluation uses classical optimization and scores document selection rather than generated answers. It does not enforce equal context budgets. The quantum wrapper exists but is not the basis of the reported experiments.

Reuse those components after verification. Replace script-only orchestration with an importable package and configuration-driven runner. Correct documentation claims that imply demonstrated quantum advantage, automatic answer improvement, or substantial sparsification without supporting measurements. Keep the historical scripts available and label what they actually evaluate.

The reported laptop has a Ryzen AI 7 350, approximately 22 GiB RAM and an RTX 5060 Mobile/Max-Q; professor-supported external compute may be available. The current tool environment could not communicate with NVIDIA through nvidia-smi. This does not establish that the host driver is broken: verify GPU visibility, VRAM, CUDA and PyTorch support on the actual execution host before selecting models. CPU-only functional development remains possible.

Planning assumption: 15–20 focused hours per week, approximately 250–330 hours through submission preparation. Weekly availability is not yet confirmed. Automated compute time is additional and will be estimated from pilots. External compute availability does not authorize purchases. Obtain a bounded allocation with the professor before paid runs.

**3. Research decisions before method development**

R1. Review roughly 15–25 closest papers, with backward and forward citation searches. Record the question, representation, objective, constraints, solver, datasets, answer metrics, hardware, resource accounting, code and limitations. Separate author claims from results we independently reproduce.

R2. Reproduce the closest available QUBO evidence-selection baseline at small scale or document why reproduction is unavailable. Do not describe our own approximation as an exact reproduction. Maintain a one-page explanation of how the proposed contribution differs from the closest work.

R3. Define three distinct hypotheses: graph features improve evidence modeling; evidence-guided sparsification improves the quality/resource tradeoff; QAOA behaves differently from classical solvers on these formulations. Test them separately. Quantum superiority is not assumed.

R4. If the exact proposed method is already covered, choose a narrower unresolved question before implementing it. If the method produces no useful tradeoff, consider a rigorous benchmark or negative-result contribution only when it reveals a generalizable phenomenon across settings. Do not manufacture a positive claim through selective reporting.

Starting primary sources: [QUBO evidence selection](https://arxiv.org/abs/2607.12334), [SetR](https://aclanthology.org/2025.acl-long.861/), [GRiever](https://aclanthology.org/2025.emnlp-industry.174/), and [QAOA sparsification](https://arxiv.org/abs/2406.14330). These establish overlap; they do not prove that our narrower hypothesis is new.

**4. Architecture and interface boundaries**

The common pipeline is:

```text
Versioned source documents
  → token-aware chunks with provenance
  → embedding cache and persistent search index
  → query retrieval and optional reranking
  → one shared candidate pool
  → evidence graph and common optimization instance
  → interchangeable classical/quantum selectors
  → validated, consistently ordered context
  → common answer generator
  → evaluator, per-question records and aggregate analysis
```

An initial selection-only mode bypasses corpus retrieval and uses the supplied candidate pool. A separate corpus mode tests retrieval and selection together. The demonstration service calls the same library used by experiments, rather than reimplementing it.

Proposed package organization:

```text
src/qrag/
  data/          schemas, dataset adapters, splits, chunking
  retrieval/     embeddings, cache, FAISS index, BM25, reranking
  evidence/      extraction, entity resolution, graph, pair features
  optimization/  objective, budgets, MILP, exact, heuristics, sparsifiers
  quantum/       Ising mapping, QAOA, mixers, backends, resource accounting
  generation/    chat prompts, model adapter, context packing
  evaluation/    answers, evidence, feasibility, statistics, errors
  experiments/   configuration, runner, manifests, resume, reporting
  api/           FastAPI request/response models and service
configs/         development, baseline, ablation and quantum configurations
tests/           correctness, invariants, integration and offline fixtures
paper/           bibliography, manuscript, generated tables and figures
docs/            decisions, reproduction guide and learning log
```

Use typed data structures and validated configuration. A minimal contract includes:

| Object | Required information |
| --- | --- |
| Document / Chunk | Stable ID, source ID, text, title, sentence or character offsets, content hash |
| QueryInput | Question ID and text, candidate chunks; no answer or relevance labels |
| EvaluationLabels | Reference answers and supporting-fact annotations, loaded only by evaluation |
| RetrievalResult | Candidate IDs, scores, embeddings or their cache references, retrieval settings |
| SelectionProblem | Candidate IDs, linear and pair coefficients, budget definition, token costs, feature provenance |
| SelectionResult | Selected IDs, feasibility, original and surrogate energies, solver status, timing, resource measurements |
| GenerationResult | Answer, supplied source IDs, input/output token counts, model/prompt revisions, timings |
| RunManifest | Code/config/data/model identifiers, seeds, environment, hardware, actual settings, output references |

Enforce boundaries in interfaces and tests: the graph builder and selector cannot accept evaluation labels. A result with an invalid budget or unknown chunk ID fails validation instead of silently reaching generation.

**5. Milestone A — reproducibility and research protocol, November 5–8**

Work:

1. Capture the current code revision, local modifications and environment without overwriting existing work. Preserve the current development examples as inspected material.
2. Inventory Python/package compatibility, GPU access, usable memory and model caches. Pin a tested dependency set, including transitive dependencies, after checking imports and smoke runs. Do not treat the current environment as tested merely because package versions can be read.
3. Create the package entry point, validated config, seeded experiment runner, structured logging and artifact directory contract. Add small offline fixtures and CI for tests that require no model downloads.
4. Define primary answer metrics, budget modes, comparison pairs, split policy, failure reporting and a first compute estimate. Create the literature matrix and paper outline.

Completion criteria: a tiny fixture experiment can run from one entry point; malformed configuration fails clearly; every output identifies its configuration and dataset; CI can run correctness tests. Produce a hardware report and contribution shortlist. No research superiority claim is required at this stage.

Teaching: package/module boundaries, dependency locking, random seeds, configuration, manifests and Git. Interview checkpoint: why do fixed seeds and pinned dependencies still fail to guarantee bit-identical results on different hardware?

**6. Milestone B — trustworthy data and answer evaluation, November 9–15**

Work:

1. Adapt the existing HotpotQA JSON to a shared schema. Preserve titles, source sentence indices and answers separately from inference inputs. Validate IDs, annotation mappings, duplicates and malformed examples.
2. Keep already inspected examples in development. Reserve new labeled examples for final evaluation, respecting the original dataset partitions; explicitly distinguish a held-out subset of official development data from the official hidden test set. Freeze ID lists and text hashes. Check exact/near duplicates and disclose remaining contamination limitations.
3. Implement dataset-compatible answer normalization, exact match and token F1, including HotpotQA's special handling of yes/no/noanswer. Compare fixtures with the official evaluator. Keep answer scores separate from document-selection scores.
4. Measure supporting-document recall and whether all annotated supporting documents are present. Do not call document recall sentence-level supporting-fact F1. Add sentence-level scoring only when the system actually predicts supporting sentences.
5. Standardize Qwen generation using its expected chat format, deterministic settings for controlled comparisons and a short-answer instruction. Record the exact prompt and input IDs. Budget space for instructions, question, context and generated tokens; reject or repack overlong inputs explicitly rather than silently truncating them.
6. Save question-level predictions, evidence IDs, metrics, errors and stage timings. Include empty-context and gold-evidence oracle diagnostics; the oracle uses labels only as a clearly labeled evaluation upper-bound experiment.

Completion criteria: metric fixtures agree with the official scorer; a small development run produces actual generated answers and scores; label-bearing objects never enter inference; failures remain in the report rather than disappearing from averages. Generation works on a recorded CPU or GPU backend.

Teaching: annotation granularity, leakage, dataset splits, normalization, EM/F1, chat templates and context limits. Interview checkpoint: what does strong performance with oracle evidence but weak performance with selected evidence suggest?

Dataset references: [HotpotQA and official evaluation resources](https://hotpotqa.github.io/); [MuSiQue repository](https://github.com/StonyBrookNLP/musique). Follow dataset-specific licensing and evaluation instructions.

**7. Milestone C — reliable retrieval, caching and first fair baselines, November 16–22**

Work:

1. Implement token-aware, sentence-respecting chunking with original offsets. Choose size/overlap on development data within the embedding model's actual input limit, including special tokens and title prefixes. Preserve supporting-fact mappings through chunking. Detect and report query/passage truncation.
2. Cache document embeddings by content hash, immutable model revision, tokenizer/preprocessing/chunk policy, normalization and relevant numeric settings. Changing any representation-defining setting invalidates its entries. Cache query embeddings separately. Validate dimensions and incomplete/corrupt entries.
3. Persist a FAISS index with matching chunk metadata and version checks. Start with an exact index so approximate-search errors do not confound selector experiments. Use SQLite for metadata where persistent filtering/provenance is needed.
4. Add relevance ranking, a lexical BM25 baseline, hybrid candidate retrieval and one fixed reranker. Treat candidate retrieval as shared and frozen for primary selector comparisons. Evaluate retriever/reranker changes separately.
5. Implement fixed-count selection and token-budget selection as separate modes. Use exactly k when feasible in fixed-count mode, with an explicit policy for pools smaller than k. Record actual context tokens in budget mode. Count with the generator's tokenizer; check the final assembled prompt because tokenization is not perfectly additive across formatted boundaries.
6. Define candidate input ordering and final context ordering, deterministic tie-breaking, document deduplication, and chunk-to-document aggregation. Apply the same rules to competing selectors.

Completion criteria: repeated document encoding produces cache hits; altered model/text/policy produces misses; a restored index retrieves the same IDs; no undocumented passage truncation; every baseline respects its declared budget. A development report shows real answer metrics and tokens for comparable selections.

Teaching: embeddings versus indexes, content-addressed caches, invalidation, hybrid retrieval, reranking, GPU batching and throughput versus latency. Interview checkpoint: why can a perfectly valid cached embedding still be incompatible with a newly loaded index?

**8. Milestone D — classical optimization and evidence modeling, November 23–December 6**

Professor's ILP/MILP suggestion is included as the main classical optimization reference. These are operations-research methods, not primarily statistical methods. Implement through SciPy/HiGHS initially; a commercial solver is unnecessary for the first study. [SciPy MILP interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).

Work:

1. Separate the objective coefficients from solver-specific representations. Reproduce the existing relevance–redundancy energy in a single tested evaluator, with a clear upper-triangular pair convention.
2. Add native cardinality and linear token constraints for classical methods. Linearize each binary product with y_ij in [0,1], y_ij <= x_i, y_ij <= x_j and y_ij >= x_i + x_j - 1. Retain the original x variables as binary. Validate linearization using exhaustive enumeration on tiny instances with positive and negative coefficients.
3. Implement MILP result status, incumbent energy, best bound, optimality gap, time limit and failures. Call a solution optimal only when the solver certifies it. Keep exhaustive search for tiny correctness cases; it is not the scalable classical baseline.
4. Add MMR, greedy coverage and simulated annealing/local search, including feasible moves for fixed-k problems. Record their budgets and multiple seeds where stochastic.
5. Build a small candidate-local entity/relation graph with source provenance. Start with linked mentions and explicitly name this an entity-link graph if semantic relations are not yet extracted. Add typed relation extraction only where development error analysis supports the extra cost. Every extracted relation points back to a source span.
6. Distinguish that knowledge graph from the passage-interaction graph used by the optimizer. Derive query-conditioned passage complementarity from short evidence paths and support estimates; shared entities alone do not prove useful complementarity. Measure alias-resolution and relation errors on a manually checked development sample.
7. Introduce graph features into the common objective and evaluate them using classical solvers first. Feed the same features to classical and quantum solvers later. Cache graph extraction with text, extractor/model, prompt and configuration revisions.

Completion criteria: MILP agrees with exhaustive optima within numerical tolerance on tiny instances, feasibility is independently checked, inference is invariant to changes in stored gold labels, and every graph edge has provenance. Report graph construction time and whether graph features affect answer quality under matched budgets.

Teaching: ILP/MILP, linearization, branch-and-bound, bounds versus incumbents, graph representations, entity resolution and source provenance. Interview checkpoint: if a graph objective helps MILP and QAOA equally, what contribution has been established?

**9. Objective and candidate research method**

Use a minimal common objective before adding more terms:

```text
E_full(x) = -alpha * sum(relevance_i * x_i)
            + sum((beta * redundancy_ij - gamma * complementarity_ij) * x_i * x_j)
```

All coefficients are computed from permitted inference inputs and development-frozen estimators. Record scaling because it affects weights, penalties and optimization behavior. Start with gamma=0 as the existing-formulation control. Coverage or higher-order terms are extensions only when justified; adding them changes complexity and may require auxiliary variables.

The sparse surrogate retains a subset of pair coefficients through a binary mask M_ij. A candidate evidence-guided rule ranks interactions using coefficient importance and the participation of their passages in short query-relevant paths, then keeps a development-selected edge budget. Preserve the sign of retained coefficients. Specify what happens when the protected set exceeds that budget; never exceed it silently.

Compare against the full graph, seeded random removal, largest-absolute-coefficient retention and a degree-controlled/top-neighbor rule with an explicit symmetry policy. Match retained-edge budgets, while also comparing actual compiled gate budgets. Include preprocessing costs.

Removing terms changes the objective. Always evaluate returned bitstrings with both E_full and the sparse surrogate. For solver comparisons, use the same objective and feasible set. For sparsifier comparisons, use the same full target for reporting. A lower sparse energy cannot establish improvement over a different dense energy scale. Sparsifying interactions generally does not reduce the number of candidate qubits.

Optional mathematical check: if the absolute sum of removed pair coefficients is delta, then |E_full(x) - E_sparse(x)| <= delta for binary x. With the same feasible set, an epsilon-suboptimal sparse solution has full-objective gap at most 2*delta + epsilon. Verify assumptions and proof as a sanity bound; do not claim this elementary bound as a novel theorem or an answer-quality guarantee.

**10. Milestone E — actual QAOA and complete resource accounting, December 7–20**

Work:

1. Verify the QUBO-to-Ising transformation, offsets, bit order and returned candidate IDs against exhaustive energies on tiny instances. Preserve negative complementarity terms correctly.
2. Run QAOA on actual development selection problems, not only a synthetic toy. Start with p=1 and p=2, seeded initialization, explicit shot counts and optimizer-evaluation budgets; choose final budgets through profiling. Record all attempted seeds and failures.
3. Compare a standard constraint-penalty approach with an existing cardinality-preserving mixer if feasible. Verify that the initial state and mixer preserve k. Count state-preparation and mixer costs. Budget inequalities need a separately documented encoding; quantum token-budget encoding is conditional on feasibility and is not silently represented as fixed-k selection.
4. Audit the constraint warning: the squared fixed-k penalty creates all-pairs couplings. A sparse semantic graph is insufficient if the complete circuit is dense again. Account for auxiliary qubits, routing, gates, depth and feasibility after encoding and compilation.
5. Keep ideal, shot-based, noisy and hardware execution modes distinct. Log backend/simulator versions, basis gates, connectivity, compilation settings/seeds, shots, parameter evaluations and total runtime. Compare compiled circuits on the same target.
6. Distinguish the energy used for parameter training from the full target used to evaluate measured bitstrings. Record how many samples were considered when choosing the final feasible selection. Repair, rejection and postselection policies must be identical or separately ablated, with their costs included.

Completion criteria: QAOA appears in genuine answer/evidence experiments; every result identifies execution mode and full circuit costs; invalid solutions are counted; objective bookkeeping agrees with independent checks. No simulator runtime is presented as a quantum hardware speedup. [IBM QAOA workflow](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm).

Teaching: qubits and measurement, Ising mapping, variational circuits, classical parameter optimization, shots, mixers, compilation and noise. Interview checkpoint: how can an edge-sparse objective still produce a costly circuit?

**11. Milestone F — candidate method and development decisions, December 21–January 3**

Implement the evidence-guided sparsifier with the explicit edge budget and fallback rules described above. Run a development factorial comparison: base versus graph objective; full versus generic versus evidence-guided sparsification; MILP/heuristic versus QAOA. Tune only the small set of parameters justified by the pilot.

Primary decision: is there a useful quality/resource frontier, meaning fewer resources at comparable quality, or better quality at comparable resources? Set the acceptable answer-quality loss and primary comparison before final evaluation. For example, a one-percentage-point F1 tolerance could be discussed, but it is not a chosen threshold or a promised result. Retention/noninferiority claims require an appropriate paired interval relative to the frozen tolerance, not simply a nonsignificant difference.

Completion criteria: a precise algorithm description, development plots, ablations, failure taxonomy and an honest continue/pivot decision. Reject unsupported claims that fewer symbolic edges imply fewer compiled gates, or that graph gains demonstrate a quantum benefit.

Teaching: ablations, controlled comparisons, Pareto tradeoffs, confidence intervals and hypothesis testing. Interview checkpoint: what additional evidence is needed when removing a component causes no statistically detectable change?

**12. Milestone G — frozen evaluation and corpus experiment, January 4–24**

Freeze models, prompts, hyperparameters, graph rules, budget modes, candidate-pool construction, analysis and question IDs before the final run. After final evaluation, any method change belongs to a new declared development cycle rather than repeated tuning against the same test results.

Evaluation matrix:

| Axis | Planned settings and scope |
| --- | --- |
| Datasets | HotpotQA plus MuSiQue with dataset-specific adapters/scorers |
| Generators | Existing small Qwen as the development model; a second stronger generator after memory/compute profiling |
| Selection setting | Supplied pools for isolation; bounded, documented corpus retrieval for end-to-end evaluation |
| Budgets | Separate fixed-k and generator-token-budget studies; actual consumption reported |
| Classical selectors | Relevance, fixed reranker, MMR, greedy coverage, MILP, simulated annealing/local search; closest reproducible prior selector |
| Quantum selectors | Dense/base QAOA, generic-sparse QAOA, proposed evidence-guided QAOA |
| Quantum sizes | Small candidate pools initially 8 and up to 10 on current HotpotQA pools; 12/16 only using an explicitly larger pool from retrieval or another dataset |
| Classical sizes | Larger retrieval pools, initially 25/50/100 if profiling supports them |
| Execution | Ideal/shot-based simulation, bounded noisy subset, optional bounded hardware subset |

Do not fabricate extra HotpotQA candidates or use gold labels to guarantee support in a reduced quantum pool. Derive candidate truncation/expansion from the common retriever and report evidence lost before selection. Freeze a stratified quantum subset by observable or permitted evaluation-group criteria, never by which method wins. Use the same instances for classical/quantum comparisons; report larger classical results separately.

Use a small development pilot to estimate time and variance before choosing final sample counts. Budget an initial 50–100 development questions and roughly 500–1,000 held-out questions per dataset for classical/generation evaluation only if measured throughput permits. Quantum runs may use a smaller explicitly reported subset. These are planning ranges, not statistical guarantees. Save paired per-question predictions and show uncertainty; average repeated solver seeds within question or use hierarchical resampling to avoid treating repeats as independent questions.

For corpus mode, use an openly identified dataset-compatible or bounded corpus, with deduplication and provenance. A bounded corpus is not full-Wikipedia evaluation. Measure retrieval recall, candidate-construction cost and selector behavior separately. Apply common candidate retrieval for selector comparisons; compare retrieval changes in another experiment.

Report answer EM/token F1, evidence recall and complete annotated support coverage, actual context length, infeasibility/failure rates, full/surrogate energy, optimality bounds, stage and end-to-end timings, peak memory and quantum resources. Use exact absolute objective gaps where certified optima exist; avoid naive approximation ratios for negative or offset energies. Separate per-query preprocessing, one-time indexing and cold/model-ready/cache-hit conditions. Include timeouts in results and provide a failure policy.

Hardware study: select instances before observing hardware outcomes, record calibration/backend details and compilation, account for queue and quantum execution separately, and compare with a noise-model study where possible. If hardware access fails, report a simulation study honestly. Access to a device alone does not establish an advantage.

Completion criteria: results generated from frozen manifests; aggregate tables trace to individual predictions; all budget claims independently checked; paired uncertainty estimates and failure reports available. Two datasets and two generators are targets subject to documented compute constraints, not excuses for selectively omitting unfavorable results.

**13. Milestone H — paper analysis and minimal demonstration, January 25–February 14**

Prepare method pseudocode, architecture figure, related-work matrix, quality/resource curves, principal baseline table, ablation table and error examples. Classify failures into retrieval misses, graph errors, scoring mismatch, optimization/feasibility, generator errors and unsupported answers. Manually inspect a documented sample rather than relying solely on automatic judges.

Draft the introduction around the observed contribution, not the hoped-for result. Write methods and setup early; finish results, limitations and discussion after analysis. Explicitly distinguish quantum simulation from hardware, objective quality from answer quality and supplied-pool selection from corpus retrieval.

Build a thin local demonstration through the common library: submit a question; inspect candidate sources and graph provenance; compare selector outputs; view answer, context tokens and stage costs. Add basic FastAPI request validation, health/readiness checks and integration tests. Long quantum tasks should run as bounded background jobs rather than blocking every API request. A timeout selects a clearly labeled classical fallback; research evaluation does not silently substitute it into QAOA results.

Completion criteria: complete manuscript draft, regenerable figures/tables, local demo and a fresh-environment reproduction attempt. The demonstration must not delay a scientifically complete draft.

Teaching: error analysis, technical writing, APIs, validation, background jobs, observability and service timeouts. Interview checkpoint: which failures should trigger a classical fallback, and how can fallback accounting distort an evaluation?

**14. Milestone I — submission package, February 15–28; target March 1**

Obtain professor/coauthor review on claims, comparisons, limitations and authorship. Maintain a claim-to-evidence checklist. Address substantive gaps before formatting polish. Check artifact/data licenses, anonymity, AI-assistance disclosure, author eligibility/reviewing obligations, venue formatting and required statements.

Create a versioned release with tested installation instructions, small legal fixtures, scripts to recreate main tables/figures, result manifests and checksums. Do not bundle model weights or datasets without redistribution permission. Provide enough information to reproduce compute-heavy runs and disclose estimated resources. Execute a clean-environment smoke run and a full main-table regeneration from saved predictions.

Choose one submission route with the professor and submit through its official portal. Do not concurrently submit the same manuscript where prohibited. An arXiv posting, if consistent with venue policy and coauthor agreement, is labeled as a preprint. After reviews, prepare a point-by-point response and new experiments where needed. Accepted conference papers may require registration/presentation; journal publication may require revisions and proof corrections. March 1 is a readiness/submission target, not an acceptance promise.

**15. Venue decisions checked November 4, 2026**

| Route | Verified status | Decision rule |
| --- | --- | --- |
| [QCNC 2027](https://qcnc.org/2027/cf-papers.php) | Paper deadline November 20, 2026; quantum AI/optimization are in scope | Optional accelerated, narrower study only. On November 8 assess whether a real contribution and credible results already exist; otherwise preserve the full study. A deadline is not a reason to submit unsupported claims. |
| [ACL 2027](https://2027.aclweb.org/calls/main/) | ARR deadline January 4, 2027, AoE; later conference commitment | Stretch route only if a mature NLP contribution and draft exist in December. Main schedule does not assume readiness. |
| [SIGIR 2027](https://sigir2027.org/pages/submit-full.html) | Abstract January 14 and full paper January 21, 2027, AoE; current page no longer labels dates proposed | Stretch route if the retrieval contribution is mature by late December. Abstract is required before paper submission. |
| [Quantum Machine Intelligence](https://link.springer.com/journal/42484) | Regular journal submission route; quantum/AI scope | Recommended initial fit for a substantive quantum-method study; internal target March 1, 2027. |
| IEEE QCE 2027 / appropriate workshops | No verified relevant submission deadline recorded | Reassess only when official calls appear, checking archival status and scope. |

The journal also advertises a relevant optimization collection with a December 31, 2026 deadline. This is optional and does not replace the regular route or justify compressing the full plan. Its subscription publishing route has no APC; optional open access is paid. [Publisher publication options](https://link.springer.com/journal/42484/how-to-publish-with-us). Budget conference registration/travel separately from compute. Check all calls again before submission.

Default venue review: discuss scope now, reassess January opportunities in late December, and finalize the March route after the observed contribution is clear. Revisions and acceptance may extend months beyond submission.

**16. Post-manuscript engineering, provisionally March 2–21**

Reserve approximately 30–45 additional hours, subject to paper revisions, for a recruiter-ready release. Strengthen the FastAPI service, containerize it, add CI image/tests and one deployment target, and build a small comparison dashboard. Use SQLite for run/source metadata and FAISS for search initially; add Postgres/pgvector or Neo4j only if deployment requirements demand them.

Add structured traces with retrieval/selection/generation spans, p50/p95 latency reports, cold/cache-hit distinctions, GPU-memory profiling, rate/size limits, timeouts and source provenance. Test untrusted-document instructions and citation consistency. Do not claim prompt-injection resistance from prompt wording alone. Isolate service errors and document fallback behavior. Establish measured service targets after load testing rather than inventing latency promises.

Demonstrate model loading, batching, request concurrency and memory limits explicitly: web-server concurrency does not guarantee concurrent GPU inference is safe. Introduce an inference queue or bounded worker only when measurements justify it. Consider quantization as a separately evaluated engineering option, since it can alter answer quality.

Final presentation: a clear README, architecture and experiment instructions, short demo video, results dashboard and factual resume bullets. Replace vague claims with measured outcomes, dataset/sample sizes and conditions. Do not label the work accepted or published before that happens.

**17. Stack and scope choices**

| Capability | Initial choice | Why / extension condition |
| --- | --- | --- |
| Core | Python, typed interfaces, validated configuration | Common pipeline for experiments and service |
| Neural inference | Existing SentenceTransformers/Transformers/PyTorch | Reuse working components; pin revisions and profile |
| Search | FAISS exact index + BM25, one reranker | Strong simple retrieval and explicit candidate control |
| Metadata | SQLite + versioned files/JSONL | Persistent provenance without extra infrastructure |
| Graph | NetworkX, provenance-aware extraction | Small transparent candidate graphs; Neo4j only if necessary |
| Classical optimization | SciPy/HiGHS, enumeration for tiny validation, SA/local search | Strong comparison and independently checkable correctness |
| Quantum | Qiskit/Qiskit Algorithms/Aer, backend adapter | Simulation and optional hardware through the same contract |
| Experiment tracking | JSON manifests/predictions first; MLflow once runner is stable | Auditable results before dashboard convenience |
| Testing and automation | pytest, lint/type checks, GitHub Actions | Correctness and repeatable installation |
| Service | FastAPI/Pydantic, bounded job handling | Reusable API with explicit validation |
| Delivery | Docker, thin Streamlit or equivalent UI, one deployment target | Demonstrate a usable system with limited scope |
| Observability | Structured logs first, traces/OpenTelemetry when serving | Find bottlenecks and explain failures |

Defer fine-tuning, autonomous agents, Kubernetes, multiple vector databases, a full-Wikipedia knowledge graph and a large frontend. Introduce them only to answer a research or product requirement. This is a depth-first AI engineering project, not a checklist of tools.

**18. Correctness and verification plan**

| Risk | Meaningful verification |
| --- | --- |
| Label leakage | Alter/remove gold fields and verify identical inference features/selections; inference APIs exclude labels |
| Chunk annotation loss | Verify source offsets and supporting-fact mapping across overlapping chunk boundaries |
| Stale cache/index | Change text/model/token policy; incompatible artifacts must miss or fail clearly |
| Incorrect optimization | Exhaustively enumerate tiny constrained instances and compare MILP/QUBO energies, including negative pairs |
| Invalid quantum mapping | Verify Ising offsets, bit ordering and measured selections against classical energies |
| Budget violations | Independently count selected items and final generator prompt tokens; test empty/infeasible/overlong cases |
| Misleading solver status | Exercise optimal, time-limited, infeasible and failed paths; never infer optimality from a returned vector |
| Incorrect metrics | Official-scorer fixtures, repeated tokens, punctuation and special answers |
| Irreproducible runs | Resume interrupted runs without duplicates; reject resume under a different manifest; regenerate summaries |
| Hidden service substitution | Record fallback explicitly; keep it distinct from QAOA-only experimental metrics |

Tests protect mathematical and experimental contracts, not cosmetic implementation details. Keep fast tests offline; mark model, GPU and hardware integration runs separately. A passing toy test is not evidence of empirical superiority.

**19. Experiment artifact contract**

Each run creates a manifest, per-question JSONL records, aggregate metrics, failure records and environment information. Record code commit plus a dirty-diff fingerprint, config and dataset hashes, evaluation IDs, immutable model/tokenizer revisions, prompts, graph/cache/index revisions, seeds, hardware and actual solver budgets. Store labels separately from inference inputs.

A per-question record includes candidate/selected IDs, budget use and feasibility, extraction/retrieval/selection/generation times, answer prediction, answer/evidence scores, original and surrogate objective values, solver status/bounds, execution mode and quantum resources. Logs distinguish missing measurements from zero. Resume skips only successfully completed records with the same immutable configuration.

Planned command contract:

```text
python -m qrag.experiments.run --config configs/dev_baselines.yaml
python -m qrag.experiments.run --config configs/dev_qaoa.yaml
python -m qrag.experiments.report --run-dir <recorded-run>
```

The first implementation milestone supplies the actual commands and installation instructions. Avoid hard-coded dataset paths, parameters and output names inside notebook scripts.

**20. Learning, interviews and collaboration**

Allocate weekly effort approximately 60% to implementation/experiments, 20% to reading/writing and 20% to explanations/exercises/review. A typical working session begins with a short concept explanation and an example outside this project, then a prediction/design question, implementation, verification and a brief interview exercise. Writing and literature review start immediately.

The assistant handles scaffolding, investigation and repetitive execution; the learner should implement or explain small critical pieces, interpret results and defend design choices. The professor helps validate novelty, scope, authorship and external resource/venue choices. No messages to the professor or external submissions occur merely because this plan mentions them.

Use the existing learning log to distinguish independent explanations from coached answers. Score conceptual correctness, assumptions, tradeoffs and evidence, with the existing 0–3 rubric. Give direct feedback about errors without personal criticism. Do not interpret fluency or a repeated definition as mastery. Revisit weak concepts in subsequent sessions and maintain a mistake/decision record.

Before submission, rehearse: a two-minute project explanation; a ten-minute architecture/research defense; and a forty-five-minute mock interview covering cache invalidation, leakage, metrics, MILP status, QAOA cost, negative results, scaling and service failures. Resume claims must be explainable from the stored artifacts.

**21. First implementation backlog, in dependency order**

| Ticket | Concrete task | Acceptance condition |
| --- | --- | --- |
| P01 | Record environment, GPU access and baseline code state | Versioned report; tested execution path selected |
| P02 | Literature matrix and contribution statement | Closest work compared; novelty question and fallback explicit |
| P03 | Schemas and inference/evaluation boundary | Gold labels cannot enter normal selector input |
| P04 | Packaging, config and run manifest | One offline fixture run produces traceable artifacts |
| P05 | Answer/evidence metrics | Agreement with official metric fixtures |
| P06 | Generator adapter and context validation | Recorded actual answers; no silent truncation |
| P07 | Fixed-k relevance baseline | Exactly k distinct available candidates under explicit short-pool policy |
| P08 | Common objective and exhaustive oracle | Tiny energies and constraints independently checked |
| P09 | MILP and token-budget baseline | Oracle agreement, verified feasibility, solver status recorded |
| P10 | Embedding cache, chunks and index | Correct invalidation/provenance and restored retrieval |
| P11 | Development baseline report | Answers, evidence, budgets, failures and timings compared |
| P12 | Graph features and first actual QAOA run | Features shared across solvers; circuit/resources recorded |

P01/P02 can proceed independently. P03–P06 establish trustworthy measurement. P07–P11 produce the first research baseline; graph and quantum-method experiments depend on it. Cache/index work can follow correctness-first small experiments rather than blocking them. The acceptance milestone for the first working research slice is generated-answer evaluation of a fair relevance baseline and a constrained classical optimizer, with manifests and no label leakage. That slice supports the later quantum study; it is not the final claimed contribution.
