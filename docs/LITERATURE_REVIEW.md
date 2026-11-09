# Literature comparison and contribution boundary

Checked November 10, 2026. The matrix records primary-source method descriptions; it is not a claim of independent reproduction. Closest work was read beyond the abstract where accessible. Broader rows are abstract-level context and require deeper comparison before submission. Numbers from different generators or pools are not comparable to our experiments.

| Primary source | Mechanism and experimental object | Relationship to this study / reproduction status |
| --- | --- | --- |
| [QUBO evidence selection, 2026](https://arxiv.org/html/2607.12334v1) | Requirement support, coverage, redundancy and complementarity; HotpotQA answer evaluation; simulated annealing | Closest formulation overlap. Different semantic estimators and budgets prevent an exact reproduction here. No released author implementation was identified on the inspected paper page. A local requirement-coverage adaptation must be labeled an adaptation. |
| [SetR, ACL 2025](https://aclanthology.org/2025.acl-long.861/) | LLM identifies information requirements and selects passage sets | Establishes set selection as prior work. [Author code](https://github.com/LGAI-Research/SetR) available; original API/model configuration is not equivalent to a small local model. |
| [GRiever, EMNLP Industry 2025](https://aclanthology.org/2025.emnlp-industry.174/) | Low-resource multi-step graph retrieval | A graph feature alone is not novel; retrieval must be controlled separately from selection. Not reproduced. |
| [QAOA sparsification, Quantum 2026](https://arxiv.org/abs/2406.14330) | Graph sparsification/decomposition for Max-Cut compilation and noise | Closest quantum resource overlap. Our signed selection objective and constraints require separate accounting. Not a new sparsification theorem. |
| [RAG, 2020](https://arxiv.org/abs/2005.11401) | Learned retrieval plus generation on knowledge-intensive tasks | Foundational architecture; our work does not train that original model. |
| [DPR, 2020](https://arxiv.org/abs/2004.04906) | Dual-encoder dense passage retrieval | Motivates vector retrieval; our frozen MiniLM is a different encoder. |
| [HippoRAG, 2024](https://arxiv.org/abs/2405.14831) | Knowledge graph plus personalized PageRank for multi-hop retrieval | Demonstrates graph retrieval overlap; not a QAOA selector. Not reproduced. |
| [HippoRAG 2, 2025](https://arxiv.org/abs/2502.14802) | Deeper passage integration and online LLM use for memory/retrieval | Stronger graph context; outside the laptop baseline scope as an exact reproduction. |
| [GraphRAG, 2024](https://arxiv.org/abs/2404.16130) | Entity communities and summaries for global questions | Global summarization differs from selecting fixed multi-hop evidence pools. |
| [LightRAG, 2024](https://arxiv.org/abs/2410.05779) | Graph and vector structures with dual-level retrieval | Relevant engineering/graph comparison; not an interchangeable solver baseline. |
| [RAPTOR, 2024](https://arxiv.org/abs/2401.18059) | Recursive clustering/summaries form a retrieval tree | Changes retrieval units; cannot attribute its results solely to subset optimization. |
| [Lost in the Middle, 2023](https://arxiv.org/abs/2307.03172) | Measures sensitivity to relevant-context position | Requires a shared ordering policy and explicit length reporting. |
| [IRCoT, 2023](https://arxiv.org/abs/2212.10509) | Interleaves reasoning and retrieval | Adds iterative generation/retrieval cost; not part of a frozen-pool solver comparison. |
| [Self-RAG, 2023](https://arxiv.org/abs/2310.11511) | Trained reflection tokens control retrieval/generation | Requires a different trained model; not reproduced. |
| [Sparse RAG, 2024](https://arxiv.org/abs/2405.16178) | Sparse context selection to accelerate RAG inference | Compression/selection efficiency is prior work; our claim must concern the quantum encoding tradeoff. |
| [QAOA, 2014](https://arxiv.org/abs/1411.4028) | Alternating cost and mixing operators | Algorithmic foundation, not our invention; no generic practical advantage follows. |
| [Alternating operator ansatz, 2019](https://arxiv.org/abs/1709.03489) | Mixers constrained to feasible subspaces | Existing basis for count-preserving mixers. Preparation/mixer costs remain included. |
| [HotpotQA, 2018](https://aclanthology.org/D18-1259/) | Multi-hop questions with supporting sentences | Use original sentence IDs and official metric semantics. Supplied pools are not corpus retrieval. |
| [MuSiQue, 2022](https://aclanthology.org/2022.tacl-1.31/) | Composed questions designed to require connected reasoning | Second dataset, answer aliases and paragraph annotations need a separate adapter. |

## Closest-work reproduction decision

The QUBO paper includes support-estimation and coverage variables beyond the prototype. Copying only its relevance/redundancy terms is not a reproduction of the full method. We will implement a transparent local requirement-coverage comparator and state its estimator differences. SetR's author repository is available, but changing its underlying LLM changes the experiment. Original-model reproduction and independent author-result validation remain limitations unless actually executed.

## Candidate contribution

The candidate is a controlled, encoding-aware study: protect question-linked interactions while removing other pair terms; compare matched edge budgets and actual compiled resources; quantify failures when a cardinality penalty makes the circuit dense again. MILP and heuristics identify formulation effects; QAOA identifies behavior under quantum circuit restrictions. Improvements in answer F1, if observed, must be supported by paired records and intervals. Negative results can still reveal where graph protection or encoding fails, but publishability requires a generalizable finding and independent review.

## Search limits

Searches covered QAOA/RAG evidence selection, QUBO selection, graph retrieval and sparsification, followed references from the closest paper and inspected newer related retrieval results. This is a 19-source initial matrix, not an exhaustive citation graph or a novelty certificate. The paper must cite any newly identified closer work before submission. No unattributed copied text or author performance numbers are used as local results.
