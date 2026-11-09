# An Encoding-Aware Evaluation of Sparse QAOA Context Selection for Multi-Hop RAG

Research manuscript draft. Author details and submission formatting require final approval. All quantum execution in this study is classical simulation.

## Abstract

<!-- BEGIN ABSTRACT -->
Final numerical abstract is generated after the frozen evaluation finishes.
<!-- END ABSTRACT -->

## 1. Introduction

Retrieval augmented generation supplies external passages to a language model. For a multi-hop question, a useful context may require several passages that jointly provide a reasoning chain. Ranking each passage independently can omit a bridge. Selecting a subset jointly is therefore a reasonable optimization problem, but a mathematically low energy need not imply a correct answer. The objective remains a proxy for useful evidence.

Quantum approximate optimization offers a way to sample low-energy binary decisions using a parameterized circuit. Its practical cost depends on the complete encoding, not only the number of terms in a semantic scoring model. In particular, a squared cardinality penalty creates couplings between every pair of candidates. Removing semantic interactions may therefore fail to reduce the circuit's interaction count. A count-preserving mixer avoids that penalty but introduces preparation and mixer costs of its own.

We investigate these effects in a controlled context-selection pipeline. Our questions are separate: whether a graph-derived pair feature transfers to answer quality; whether protecting possible evidence links helps sparsification at the same retained-edge budget; and how constraint encoding changes feasibility and compiled cost. We compare classical optimization, heuristics, uniform feasible sampling and actual QAOA simulations. We do not assume a quantum advantage or describe fewer symbolic edges as a demonstrated hardware improvement.

The contribution is a reproducible, encoding-aware empirical evaluation with question-level answer outcomes, full-objective bookkeeping and complete circuit compilation. The graph signal is deliberately transparent and limited: it uses entity links with exact source spans, not verified semantic relations. The evaluation includes unfavorable outcomes and a documented implementation restart. Publication novelty and significance remain subject to external review.

## 2. Related work and comparison boundary

RAG combines retrieval with generation [1], and dense passage retrieval establishes a widely used vector-search approach [2]. SetR treats retrieval output as a set chosen to satisfy information requirements [3]. Requirement-aware QUBO evidence selection already combines relevance, coverage and complementarity and reports downstream QA experiments using unconventional-solver-compatible formulations [4]. We therefore do not claim that QUBO evidence selection itself is new. Our lexical coverage comparator is not an exact reproduction of either method's semantic estimators or original model configuration.

Graph retrieval systems such as GRiever and HippoRAG show that graph structures can support multi-hop retrieval [5,6]. Their retrieval architectures differ from an interchangeable selector over one frozen candidate pool. We keep supplied-pool selection separate from bounded corpus retrieval. Context position can also affect generation [7], so competing selectors use a common ordering policy.

QAOA and the alternating operator ansatz provide the algorithmic foundations [8,9]. Prior sparsification work studies QAOA compilation and noise for Max-Cut [10]. Our signed relevance/complementarity objective and context-budget constraints require separate evaluation; the elementary coefficient-removal bound used below is a sanity check, not a new theorem. A complete 19-source comparison matrix accompanies the software.

## 3. Problem and representations

For question q and candidates p_1 through p_n, let x_i be 1 when passage i is supplied to the generator. Inference inputs contain question text, source text and provenance. Reference answers and supporting annotations are loaded into separate evaluation objects. Graph construction, candidate reduction and normal selection cannot access these annotations.

The frozen MiniLM encoder has a limited input length. We form sentence-aware chunks of at most 240 embedding tokens including a bounded title prefix. Oversized sentences use overlapping offset windows. Every chunk retains its original character range and sentence mapping. A passage vector is the normalized arithmetic mean of its normalized chunk vectors. This uses later passage content that the original prototype truncated, but mean pooling is itself an approximation and can dilute small relevant facts.

Relevance r_i is the inner product of unit question and passage vectors. Redundancy uses the positive part of passage cosine similarity. Candidate-title matches and capitalized spans induce an entity-link graph. Let L_ij indicate a shared extracted entity and let a_i denote the fraction of question content terms found in passage i. The complementarity proxy is:

$$
C_{ij}=L_{ij}\max(a_i,a_j)\sqrt{\max(r_i,0)\max(r_j,0)}.
$$

This feature is nonnegative but is not a probability of support. Shared names can produce false links. Source surface forms are stored separately from canonical names to preserve exact Unicode offsets. A content-addressed SQLite cache identifies embedding and graph artifacts by text, immutable model revision and preprocessing/extractor settings.

## 4. Selection objectives and constraints

The common full target is:

$$
E_{\mathrm{full}}(x)=\sum_i a_i^{\mathrm{obj}}x_i+\sum_{i<j}b_{ij}x_ix_j,
$$

$$
a_i^{\mathrm{obj}}=-\alpha r_i,\qquad b_{ij}=\beta\max(s_{ij},0)-\gamma C_{ij}.
$$

We distinguish the objective coefficient from the question-anchor notation. Alpha is 1 and beta is 0.2. Gamma is selected on development data from {0,0.1,0.2,0.4,0.8}; 0.2 gives the highest equal-weight mean development answer F1 across the two datasets. Gamma=0 is the base-formulation control. These choices are frozen before definitive held-out execution.

Fixed-count experiments impose sum(x_i)=k, with k=5 when enough candidates exist. A declared use-all policy applies when fewer are available. Separate token-budget experiments impose a linear conservative cost cap and a nonempty selection. Actual formatted context and total prompt tokens are independently checked; overlong contexts become failures rather than being silently trimmed. Equal count does not imply equal tokens, and equal caps do not imply equal consumption.

MILP introduces continuous y_ij in [0,1] with y_ij <= x_i, y_ij <= x_j and y_ij >= x_i+x_j-1. Binary x makes y equal the product regardless of the pair coefficient sign. Native count/token constraints avoid penalty encoding in the classical solver. We record incumbents, bounds, status and time limits; only a certified optimum is called optimal. Exhaustive enumeration validates tiny signed instances.

## 5. Sparse surrogates

A sparse target keeps an exact budget floor(f*m) of the m nonzero unordered pair coefficients. Linear terms are unchanged. Controls retain the largest absolute coefficients, a seeded random set, or edges prioritized by the smaller of their endpoint incident ranks. All retained signs and magnitudes are preserved.

Evidence guidance ranks linked edges by C_ij times the square root of absolute coefficient magnitude. It reserves at most half the hard budget for these possible bridges, then fills remaining slots by magnitude. If too many links qualify, only the highest-priority links fit; if none qualify, the rule becomes magnitude retention. This protection policy is a hypothesis about useful structure, not guaranteed evidence preservation.

For removed interactions R, define delta as their total absolute coefficient mass. Each binary product is at most 1, giving the bound:

$$
|E_{\mathrm{full}}(x)-E_{\mathrm{sparse}}(x)|\leq\delta.
$$

For the same feasible set, an epsilon-suboptimal sparse solution has full-objective gap at most 2*delta+epsilon. This follows by applying the bound to the returned solution and the full optimum. It says nothing about answer F1. Every returned subset is evaluated under both energies so sparse energies are never compared as if they were the same objective scale.

## 6. Quantum implementation and resource accounting

Substituting x_i=(1-Z_i)/2 yields an Ising Hamiltonian with a constant offset, single-qubit fields and pair couplings. Tests verify all basis-state energies and little-endian candidate mapping on small instances. QAOA uses p=1/2, COBYLA with a maximum of 64 function evaluations, three recorded seeds and 1,024 final samples. The main study trains exact statevector expectations; a separate development control uses finite-shot training. A bounded diagnostic applies synthetic noise only during final sampling.

The penalty encoding adds lambda*(sum(x_i)-k)^2. With B the sum of absolute original coefficients, lambda=B+1 is sufficient to make every infeasible global minimum worse than a feasible solution. This does not guarantee feasible measurements after finite shallow optimization. Expansion adds 2*lambda to every unordered pair, making the encoded cost graph dense even when the semantic graph is sparse.

The alternative starts from a seeded feasible basis state and applies a ring of RXX(beta) followed by RYY(beta) on each edge. Their paired product implements XY exchange and preserves the number of ones ideally. It is not uniform feasible-state preparation, and its shallow expressivity depends on the initial basis state. Preparation and mixer operations are included in resource counts.

There is a specific limitation of this frozen basis-start circuit. A diagonal cost unitary acting first on one computational basis state produces only a global phase. Thus the first cost angle is inactive in probabilities, and p=1 has only mixer-dependent probabilities. Its optimized mixer angle can still depend on which objective is minimized. We retain this diagnostic implementation and add an explicitly exploratory control: one fixed pi/4 XY ring sweep prepares a generally nonuniform feasible superposition before cost evolution. Its full preparation cost is compiled. This control is not presented as uniform Dicke-state preparation, a globally optimized ansatz, or a preregistered replacement for the primary comparison.

We compile complete circuits to rz/sx/x/cx with fixed settings and seeds on synthetic all-to-all and line connectivity. We report qubits, two-qubit gates, depth and feasible-shot fractions. These targets are not calibrated devices. Simulation time is a classical implementation measurement and is never presented as a quantum hardware speedup.

The final selected context is the minimum-surrogate-energy feasible measured sample, with deterministic tie-breaking and no repair. This best-of-many policy includes classical energy evaluation. A uniform feasible-sampling control uses the same number of draws. For n=10,k=5 there are only 252 feasible subsets, and 1,024 uniform feasible draws have about 98.3% probability of including one particular optimum. Larger candidate sensitivities therefore remain important even when small-case solutions look strong.

## 7. Experimental setup

We use HotpotQA and MuSiQue-Ans with dataset-specific adapters and official answer-score semantics [11,12]. Each dataset has 100 development questions and 500 fresh held-out questions from the official validation/dev partition. Earlier inspected local HotpotQA IDs are excluded. Frozen ID lists, source revisions and hashes are released; these are not hidden-test results. Exact normalized questions and token-trigram near matches were audited, but paraphrases and pretrained-model exposure remain unknown.

The main classical study evaluates two frozen Qwen generators, 1.5B and 3B, with identical settings across selectors. It includes relevance, BM25, hybrid ranking, a fixed chunk-aware cross-encoder, MMR, lexical coverage, greedy energy, annealing, random feasible sampling, full MILP and sparse MILPs. These generators share a model family, limiting architectural generalization.

The main quantum study uses the first 50 frozen IDs per dataset and a shared relevance-reduced pool of at most ten candidates. Reduction is label-independent and applies to the classical references too. Three seeds are averaged within question before paired bootstrap resampling. Five-question 12/16-candidate MuSiQue sensitivities use real supplied candidates. Token studies and bounded corpus studies have their own declared sample sizes and are not pooled with the primary count experiment.

The bounded corpora contain the deduplicated union of benchmark input passages. Exact chunk search and BM25 rank fusion construct common pools of 25/50/100 passages. This is a closed-corpus diagnostic, not full-Wikipedia retrieval. Larger MILPs use a one-second limit with status and bounds retained.

Primary task quality is mean per-question answer F1; normalized exact match and supporting-document metrics are secondary. Failures remain zero in answer denominators. Successful-only resource/evidence summaries are labeled. Confidence intervals use 10,000 paired question bootstrap resamples with seed 20261110. Seeds are repeated solver attempts, not independent questions. No noninferiority margin or family of confirmatory p-values is claimed.

An initial execution cycle was stopped after a Unicode provenance assertion failed. All definitive conditions were restarted with the same scientific settings after a targeted repair; superseded artifacts and an erratum are retained. This separates debugging from answer-based retuning.

## 8. Results

<!-- BEGIN RESULTS -->
Definitive tables and interpretation are generated only after all frozen runs finish.
<!-- END RESULTS -->

<!-- BEGIN SAMPLING -->
### Development-derived sampling mechanism study

To separate trained distribution quality from best-of-many selection, we train p=1 circuits on 20 development-derived coefficient instances at each of n=8,10,12,16, with k=5 and three seeds per encoding. These are 480 numerical circuit solves, not additional held-out answer evaluations. For single-draw optimum mass u, the probability of seeing an optimum in S draws is 1-(1-u)^S. We compute this directly from the trained ideal statevector distribution and enumerate feasible energies. This calculation does not estimate a physical device's output distribution.

| Candidates | Encoding | Uniform P(optimum), 1,024 draws | QAOA P(optimum), 1,024 draws | Conditional QAOA energy gap |
| --- | --- | ---: | ---: | ---: |
| 8 | xy | 1.0000 | 0.1178 | 0.1343 |
| 8 | penalty | 1.0000 | 0.9689 | 0.0008 |
| 10 | xy | 0.9829 | 0.0624 | 0.1647 |
| 10 | penalty | 0.9829 | 0.7415 | 0.0061 |
| 12 | xy | 0.7258 | 0.0049 | 0.2457 |
| 12 | penalty | 0.7258 | 0.1949 | 0.0472 |
| 16 | xy | 0.2090 | 0.0000 | 0.3141 |
| 16 | penalty | 0.2090 | 0.0127 | 0.1463 |

Means average seeds within question first. Conditional gaps describe the best feasible sample given that at least one is drawn; no-feasible probabilities and paired question intervals are also released. This development diagnostic compares final draws only: QAOA additionally performs angle training with up to 64 exact-expectation evaluations, whereas uniform feasible sampling does not. The same 20 questions recur across sizes, so the four size groups are not independent replications.

![Figure 2. Optimum coverage from trained ideal distributions and uniform feasible draws. These development-derived probabilities describe the full objective, not answer correctness.](figures/sampling_coverage.png)

<!-- END SAMPLING -->

## 9. Limitations and threats to validity

The entity-link proxy lacks independent semantic annotation and can reward spurious links. Its query-term anchors are lexical, not a verified decomposition of information requirements. No original-model reproduction of SetR or the closest QUBO selector is claimed. Small open generators and one embedding model limit generalization. Reference normalization can penalize semantically related answers, and reference annotations themselves can contain errors.

The quantum subset is much smaller than the classical evaluation and includes ideal training, finite-shot postselection and only bounded artificial-noise diagnostics. The count-preserving state starts in one feasible basis state. Gate counts depend on compiler target and settings; physical calibration, connectivity, readout errors, queueing and fault-tolerant overhead are absent. Larger n sensitivities are too small for broad answer-quality claims.

The full objective is a proxy. Better energy, more annotated support and better answer F1 are different observations. A sparse surrogate may change selected contexts even when its objective gap is small. The elementary coefficient bound does not establish semantic preservation. A nonsignificant paired difference does not establish equality. Resource measurements on a laptop are descriptive and do not establish industrial throughput or hardware advantage.

The original basis-start p=1 circuit is structurally weak because its first cost phase is global. Complete gate counts use a fixed generic compilation policy, not a proof of minimum circuit cost; a semantics-aware compiler could remove known-basis diagonal work. The added preparation control addresses this particular degeneracy but is exploratory. Beta is held at 0.2 while gamma receives a limited development sweep; neither the objective nor the variational circuit is claimed to be the strongest possible classical or quantum method. Question-level bootstrap intervals also do not model every dependency caused by shared source passages or question composition.

Corpora are bounded unions of benchmark inputs with known source inclusion, not a deployment-scale open collection. Question deduplication cannot eliminate source overlap or pretrained-model contamination. The service is a local demonstration with bounded jobs and labeled fallbacks; its reliability behavior is excluded from QAOA-only research results.

## 10. Reproducibility and release

The software exposes configuration-driven study and report commands, immutable model revisions, source snapshots, checksums, per-question predictions, actual prompts/token IDs, solver traces and complete-circuit resources. A durable append journal supports interrupted-write recovery and explicit failure retries without replacing successful outcomes. Compact public evidence links to hashes of full local artifacts. Raw datasets and weights are obtained from their primary hosts under their own licenses.

Tests cover official-scorer agreement, label isolation, offsets, cache/index invalidation, signed MILP correctness, quantum spectra, count preservation, feasible sampling, sparsification budgets, statistics and service failure paths. A separate FastAPI package uses the same research library, avoiding a second implementation of scientific scoring. The artifact package documents tested environments and remaining external review requirements.

AI assistance was used to develop software, orchestrate local experiments, inspect artifacts and draft technical documentation and this manuscript. This involved substantive generation beyond copy editing. Numerical statements are computed from saved artifacts rather than supplied by the assistant from memory. Human authors must independently review and take responsibility for the full methods, code, results, citations and final text before submission; that external review is not represented as completed here.

## 11. Conclusion

<!-- BEGIN CONCLUSION -->
The final conclusion follows the completed frozen evidence and is not predetermined by the proposed method name.
<!-- END CONCLUSION -->

## References

[1] Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. 2020. https://arxiv.org/abs/2005.11401

[2] Karpukhin et al. Dense Passage Retrieval for Open-Domain Question Answering. 2020. https://arxiv.org/abs/2004.04906

[3] Lee et al. Shifting from Ranking to Set Selection for Retrieval Augmented Generation. ACL 2025. https://aclanthology.org/2025.acl-long.861/

[4] Singh and Vadlamani. QUBO-Optimized Evidence Selection for Retrieval-Augmented Question Answering with Unconventional Solvers. 2026. https://arxiv.org/abs/2607.12334

[5] Melo et al. Don't Forget the Base Retriever! A Low-Resource Graph-based Retriever for Multi-hop Question Answering. EMNLP Industry 2025. https://aclanthology.org/2025.emnlp-industry.174/

[6] Jiménez Gutiérrez et al. HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models. 2024. https://arxiv.org/abs/2405.14831

[7] Liu et al. Lost in the Middle: How Language Models Use Long Contexts. 2023. https://arxiv.org/abs/2307.03172

[8] Farhi, Goldstone and Gutmann. A Quantum Approximate Optimization Algorithm. 2014. https://arxiv.org/abs/1411.4028

[9] Hadfield et al. From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz. 2019. https://arxiv.org/abs/1709.03489

[10] Moondra et al. Promise of Graph Sparsification and Decomposition for Noise Reduction in QAOA: Analysis for Trapped-Ion Compilations. Quantum 2026. https://arxiv.org/abs/2406.14330

[11] Yang et al. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. EMNLP 2018. https://aclanthology.org/D18-1259/

[12] Trivedi et al. MuSiQue: Multihop Questions via Single-hop Question Composition. TACL 2022. https://aclanthology.org/2022.tacl-1.31/
