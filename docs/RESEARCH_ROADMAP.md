**Q-RAG research roadmap — proposed, 2026-11-01**

Updated execution reference: [Detailed implementation plan, November 4, 2026](IMPLEMENTATION_PLAN.md). Use that document for the current milestone schedule, module contracts and venue decisions. In particular, the SIGIR CFP now lists January 14/21 without the earlier "proposed" label, and QCNC's November 20 opportunity is included. This original roadmap remains background context.

Publication is the first priority. This is a research plan, not evidence that the proposed method is novel, effective, or accepted for publication. No experiments or implementation changes were made while preparing this document.

**Resources and planning assumptions**

The user reports a Ryzen AI 7 350 laptop, RTX 5060 Mobile/Max-Q, approximately 22 GiB system RAM, and possible professor-funded cloud/quantum access. GPU VRAM and usable CUDA support still need measurement. There is no external project deadline. Assume 15–20 focused hours per week for planning; the user has not confirmed weekly availability. Funding availability is not authorization to incur costs.

**What the current implementation supports**

The project has dense retrieval, a relevance–redundancy QUBO, a classical exact solver, a QAOA wrapper, an LLM generator, and document-selection evaluation. The main evaluation uses the classical solver and does not evaluate generated answers. Its objective does not constrain selected document count or token budget. The QAOA wrapper uses classical statevector simulation. These are a useful starting point, but do not establish a quantum advantage or an answer-quality improvement.

**Literature constraints on the contribution**

- [QUBO-Optimized Evidence Selection for Retrieval-Augmented Question Answering with Unconventional Solvers](https://arxiv.org/abs/2607.12334), July 2026 preprint, directly overlaps relevance, coverage, redundancy, and complementarity-based evidence selection.
- [SetR, ACL 2025](https://aclanthology.org/2025.acl-long.861/) already studies passage set selection for RAG.
- [GRiever, EMNLP Industry 2025](https://aclanthology.org/2025.emnlp-industry.174/) studies inexpensive graph-based multi-hop retrieval.
- [QAOA graph sparsification and decomposition](https://arxiv.org/abs/2406.14330) already studies circuit and noise benefits of sparsification for Max-Cut.

Consequently, applying QUBO, adding a knowledge graph, or sparsifying QAOA alone is not a defensible novelty claim. Complete a comparison matrix of approximately 15–25 closest papers, including their references and later citing work, before committing to the contribution. Record formulations, datasets, solvers, constraints, quantum execution, resource accounting, and limitations. Reproduce the closest accessible method where feasible; document deviations.

**Provisional research question**

Can query-specific evidence structure guide removal of pairwise QUBO interactions so that multi-hop answer quality is preserved while compiled QAOA resource costs fall, compared with dense QAOA and generic sparsification?

Working title: Evidence-Preserving Sparsification for Quantum Context Selection in Multi-Hop RAG.

Here, sparsification means removing selected interactions. Evidence preservation is a hypothesis to test, not a guaranteed property. A candidate rule would protect interactions connecting plausible evidence chains and remove less useful interactions. Build those estimates only from the question and available document text, never gold answers or supporting-fact labels. Distinguish the entity/relation knowledge graph from the passage-interaction graph used by the optimizer.

Start with a fixed number k of selected chunks. Consider token-budget constraints after profiling and a feasibility review. Fixed document count does not equal fixed context length, so report both and conduct a token-budget comparison before making efficiency claims.

The penalty (sum(x_i) - k)^2 creates pairwise interactions between every variable pair. Token-budget encodings can introduce auxiliary variables and further interactions. A sparse semantic graph does not guarantee a sparse final circuit. Compare penalty encoding with an appropriate existing constraint-preserving mixer if feasible; include mixer gates, initial-state preparation, routing, auxiliary qubits, feasibility rates, and any repair/postselection costs. Do not claim the mixer itself as novel.

If literature already covers this exact method, or pilot results show no useful tradeoff, pivot before expensive sweeps. A rigorous benchmark of when quantum context selection fails or succeeds is an alternative only if it produces a generalizable insight, not merely a table where one solver loses.

**Professor's suggestions**

ILP is integer linear programming; MILP is mixed-integer linear programming. They belong primarily to mathematical optimization/operations research. They provide explicit budget constraints and strong classical reference solutions. Pairwise binary products can be linearized exactly: introduce y_ij in [0,1] with y_ij <= x_i, y_ij <= x_j, and y_ij >= x_i + x_j - 1. Then replace x_i*x_j with y_ij. Inspect solver status and optimality bounds; a time-limited solution is not necessarily proven optimal. [SciPy MILP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).

A knowledge graph represents entities and relationships, with source provenance. It may identify complementary passages that semantic similarity alone confuses with redundancy. Begin with a small graph over retrieved candidates, not an unrestricted ontology-building project. Graph extraction errors and preprocessing costs must be measured. Use the same graph features for classical and quantum comparisons.

**Experimental contract**

1. Separate improved scoring/formulation from improved solver performance. Run classical and quantum solvers on the same objective and candidate pools.
2. Use HotpotQA and a second multi-hop dataset such as MuSiQue. Previously inspected examples are development material; reserve a fresh untouched final evaluation split. Keep gold labels out of graph construction and selection.
3. Start with supplied candidate pools to isolate selection. Add a corpus-retrieval experiment before claiming full retrieval scalability. Report what the initial retriever missed.
4. Compare relevance ranking, reranking, MMR, greedy coverage, MILP, simulated annealing/local search, the closest reproducible prior selector, dense QAOA, generic sparsification, and the proposed method. Scope costly baselines through pilots, without quietly omitting the strongest relevant competitors.
5. Match selection budgets and generation settings. Control candidate text, prompts, context ordering policy, decoding, and model revisions. Report fixed-count and token-budget results separately.
6. Evaluate generated-answer exact match and token F1, supporting-evidence recall and complete evidence-chain coverage, selected tokens, feasibility, objective quality, end-to-end latency, and cost. Use human checks on a documented sample; automated judges are supplementary.
7. Use paired confidence intervals and predefined seeds. Choose sample sizes from pilot variance and compute measurements. Do not tune on the final evaluation set. Freeze quantum subsets before observing comparative outcomes and report their selection rule.
8. Pilot QAOA at 8, 12, and 16 candidate variables, increasing only after profiling. Report total qubits after encoding, layers, shots, optimization evaluations, compiled two-qubit gates/depth, noise settings, and seeds. Separate ideal simulation, noisy simulation, and actual hardware.
9. Compare full objective versus removed graph terms, dense versus sparse interactions, generic versus evidence-guided removal, and classical versus quantum solvers. Larger classical cases contextualize the limitations of small quantum studies.
10. Include embedding, graph construction, optimization, and generation costs. Distinguish cold runs from cached runs and quantum execution time from queue/end-to-end time. Never infer practical quantum speedup from simulator timings.

**Venue strategy, checked 2026-11-01**

| Venue | Fit and timing |
| --- | --- |
| [Quantum Machine Intelligence](https://link.springer.com/journal/42484) | Recommended initial target if the result makes a substantive quantum/AI contribution. Regular journal route; March 1, 2027 is our proposed internal submission target, not a publisher deadline. |
| [SIGIR 2027 full papers](https://sigir2027.org/pages/submit-full.html) | Stretch target for a strong retrieval contribution. The CFP explicitly labels dates PROPOSED: abstract January 14, paper January 21, 2027, AoE. Prior abstract required. |
| [ACL 2027](https://2027.aclweb.org/calls/main/) | Stretch target for a strong NLP contribution. ARR submission January 4, 2027, AoE; later conference commitment is a separate step. |
| IEEE QCE 2027 | Potential quantum conference alternative. A 2027 submission deadline was not verified; do not extrapolate the 2026 deadline. |
| Relevant 2027 workshops | Consider only after their specific CFPs appear. Verify peer review and archival publication status. |

Quantum Machine Intelligence offers subscription publication without an APC, with optional paid open access; check funding requirements and current terms before choosing. [Publisher policy](https://link.springer.com/journal/42484/how-to-publish-with-us). Submission readiness is controllable; acceptance and publication dates are not. Do not submit the same manuscript concurrently where venue policies forbid it. An arXiv preprint is not peer-reviewed acceptance.

**Proposed schedule**

| Dates | Deliverable and decision |
| --- | --- |
| November 2–15, 2026 | Literature matrix, contribution statement, hardware/throughput pilot, experiment protocol. Decide whether the novelty hypothesis survives. |
| November 16–December 6 | Reliable answer evaluation, caching/chunking, matched-budget baselines, MILP and small evidence graph. Confirm the problem is worth pursuing. |
| December 7–January 3 | Candidate sparsification method, actual QAOA experiments, circuit accounting and ablations on development data. Decide whether a January conference attempt is credible. |
| January 4–31, 2027 | Frozen experiments across datasets, seeds and generators; noisy simulation; bounded hardware study if accessible. |
| February 1–14 | Statistical analysis, error taxonomy, full draft, reproducibility run. |
| February 15–28 | Professor review, necessary corrections, artifact cleanup and final venue checklist. |
| March 1 | Proposed journal submission target; alternatively choose a verified suitable conference deadline before submission. |

Write the paper outline and methods notes from the first week. Do not wait until all experiments finish. Allocate roughly 60% of weekly time to research/implementation, 20% to reading/writing, and 20% to learning/review. Adjust scope after measuring availability and throughput.

**Engineering and teaching**

Build a reproducible Python package with typed interfaces, configuration, pinned dependencies, meaningful tests, experiment manifests, and a single experiment entry point. Add ingestion/chunking, versioned embedding caches and a persistent index. Log quality, latency, cost, model revisions, seeds and dataset hashes. Build a small FastAPI service, Docker image, CI checks, and a thin demonstration UI after the research core is dependable. Profile GPU batching and memory before requesting cloud resources. Use a classical fallback when quantum execution is unavailable or violates the service budget.

NetworkX is enough for the initial candidate graph; Neo4j is conditional on a genuine graph persistence/query need. FAISS is suitable initially; a database-backed vector store is conditional on service requirements. Add structured logs/traces, timeouts, document provenance, and tests for untrusted document instructions. Kubernetes, fine-tuning and multi-agent systems are optional extensions, not publication prerequisites.

For each feature: explain the concept and a transferable example, ask for a prediction/design choice, implement together, verify it, and ask conceptual, debugging and design interview questions. Track actual answers in LEARNING_LOG.md; never infer mastery from having received an explanation. Revisit weak areas during later work. No recurring reminder has been scheduled.

**Submission process**

Agree with the professor on contributions/authorship, target venue, and budget early. Study its recent papers and author instructions. Write the question, prior-work distinction, method, experiment protocol, results, ablations, limitations and reproducibility details. Prepare code/data instructions subject to licenses and anonymization rules. Submit through the venue's official portal; respond to reviewers point by point; complete revisions, final formatting and presentation requirements after acceptance. Keep resume labels accurate: in preparation, submitted, preprint, accepted, or published.
