# Technical foundations and implementation notes

**Version 0.1 | Updated November 9 2026**

This companion explains the mathematics, ML concepts and engineering decisions behind the working baseline. It connects definitions to source functions, derives the important equations and provides numerical examples. [Research progress](RESEARCH_PROGRESS_REPORT.md) contains the concise experimental account; [Development sequence](DEVELOPMENT_SEQUENCE.md) records how the current system was assembled.

Coverage follows the implementation rather than the full proposed architecture. The current runner uses supplied passage pools, MiniLM, fixed-count ranking or MILP, and Qwen generation. Graph features, corpus retrieval, persistent embedding caches, token-budget selection and integrated quantum experiments are future work. Sections describing them are explicitly labeled.

**Contents**

- [System and evidence](#the-system-and-the-problem-it-solves)
- [Data contracts and labels](#data-contracts-and-label-isolation)
- [Tokens embeddings and transformers](#tokens-embeddings-and-transformer-representations)
- [Similarity and array shapes](#similarity-derivation-and-array-shapes)
- [Selection objective and numerical example](#the-selection-objective-and-its-interpretation)
- [MILP derivation and bounds](#from-binary-quadratic-optimization-to-milp)
- [Generation and inference](#answer-generation-and-inference-behavior)
- [Evaluation calculations](#evaluation-with-worked-calculations)
- [Reproducibility and software contracts](#reproducibility-and-software-contracts)
- [Actual question trace](#a-complete-trace-through-the-actual-first-question)
- [Planned graph and quantum foundations](#foundations-for-the-planned-graph-and-quantum-work)
- [Upcoming engineering](#upcoming-engineering-concepts-and-their-status)
- [Technical review questions](#technical-review-questions-and-reasoning-checks)
- [References](#sources-and-implementation-references)

## The system and the problem it solves

A language model can generate fluent text without having the evidence required for a question. Retrieval augmented generation supplies source material as part of its input. In this project, context selection is the decision about which candidate passages reach the generator.

The implemented flow is:

~~~text
Processed question and candidate passages
  → separate inference inputs from reference annotations
  → embed the question and candidates
  → calculate relevance and pair similarities
  → construct a common constrained selection problem
  → select passages by ranking or MILP
  → order selected passages consistently and construct a chat prompt
  → generate a short answer
  → evaluate against reference annotations and save artifacts
~~~

This is initially a selection experiment: the dataset supplies the candidate pool. Searching a large corpus to obtain that pool is a different stage and is not implemented in the new runner.

Three questions must remain separate. Is useful evidence present among the candidates? Does the selector retain it? Can the generator answer from the selected context? A wrong answer can originate at any of these stages.

### A running evidence example

Consider a fictional question: In which country was the director of Film A born?

| Passage | Information | Role |
| --- | --- | --- |
| A | Film A was directed by Maya Rao | Identifies the person |
| B | Maya Rao was born in Jaipur India | Supplies the requested country |
| C | Film A was released in 2010 | Related topic but insufficient for this question |

A and B jointly support India. Their relationship is complementary. Two passages repeating the release date are redundant for this question. Topic similarity alone cannot reliably distinguish these cases.

This example illustrates the task; it is not a measured benchmark result.

## Data contracts and label isolation

**Implementation:** [data.py](../src/qrag/data.py), functions adapt_example and load_examples.

The source JSON contains both usable input and evaluation information. adapt_example splits it into:

| Object | Contents | Consumer |
| --- | --- | --- |
| Document | ID title text | Scoring selection generation |
| QueryInput | Question ID question text document tuple | Inference pipeline |
| EvaluationLabels | Reference answer and supporting-title set | Evaluator |

The reference answer and is_relevant fields are absent from inference objects. The adapter obtains supporting titles from supporting_facts, with a fallback to existing relevance annotations, but places them only in EvaluationLabels.

This boundary prevents the normal pipeline from being handed the answer key. The label-isolation test changes the references and relevance flags while keeping text unchanged, then verifies that QueryInput is identical. That test protects the adapter contract; it is not a universal proof against all possible leakage, model pretraining contamination or future misuse.

The current adapter validates nonempty fields, distinct titles within a question and distinct question IDs across the dataset. It does not yet preserve sentence offsets in Document or perform full near-duplicate detection. These are remaining requirements.

Frozen dataclasses make field reassignment difficult, but type annotations do not automatically validate values. Runtime checks in the adapter and configuration are separate. See the [Python dataclass documentation](https://docs.python.org/3/library/dataclasses.html).

**Transferable application:** the same separation applies to recommender evaluation, fraud detection and forecasting: fields available only after the outcome must not enter the prediction input.

## Tokens embeddings and transformer representations

### Tokens and context limits

A tokenizer maps text to a sequence of integer token IDs. Tokens can represent subwords or other text units; token count is not word count. Different models can tokenize the same text differently.

Each model has an input limit. If a necessary fact lies beyond the part an embedding model reads, that fact cannot contribute to its relevance score even if the full passage later reaches the generator.

The new model adapter counts embedding input tokens before encoding. With embedding_truncation set to error, an overlong question or passage produces a visible failure. The report mode explicitly records affected positions before allowing truncation. Neither mode implements chunking.

Chunking will divide long text into smaller, traceable units. It needs source offsets and annotation mappings so that evaluation can still determine which facts survived. Overlap can protect boundary facts but also creates repeated material that affects selection and token usage.

### What the embedding model produces

The configured SentenceTransformer maps each text to a 384-dimensional vector. Its model card describes a transformer followed by mean pooling; the repository delegates those operations to the pretrained model rather than implementing or training them. [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

To understand the representation, consider token features H and one attention head:

$$
Q=HW_Q,\quad K=HW_K,\quad V=HW_V,
\qquad
\mathrm{Attention}(Q,K,V)
=\mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}+M\right)V.
$$

Q and K determine attention weights; V supplies values to combine. M masks disallowed positions. Multiple heads and learned layers build contextual token representations. This is the general transformer mechanism, not a replacement for the model's full architecture [Attention paper](https://arxiv.org/abs/1706.03762).

For one head with T tokens, Q and K have shape T × d_k, so QKᵀ is a T × T table of token interactions. Softmax is applied across each row:

$$
\mathrm{softmax}(z)_j=\frac{e^{z_j}}{\sum_m e^{z_m}}.
$$

It converts that row's scores into nonnegative weights summing to one. Those weights describe an internal computation, not the probability that a source claim is true. Encoder attention can use both directions of context, while a causal generator masks future token positions.

For T token vectors hₜ and a valid-token mask mₜ, masked mean pooling has the form:

$$
z=\frac{\sum_{t=1}^{T}m_t h_t}{\sum_{t=1}^{T}m_t}.
$$

Padding must not contribute to the mean. The pooled vector is then normalized for this project's similarity calculations.

An embedding is a learned representation, not a list of explicit verified facts. Close vectors suggest related representations; they do not certify factual agreement, answer sufficiency or source reliability.

### Pretrained inference and training

The current project loads pretrained weights and performs inference. It does not fine-tune MiniLM or Qwen. Inference computes outputs using existing parameters; training changes parameters using a learning objective and an optimizer.

This distinction also separates two kinds of optimization in the project: MILP chooses passage-selection variables, whereas neural-network training would change model weights. QAOA's classical optimizer would adjust circuit angles, not the LLM weights.

## Similarity derivation and array shapes

**Implementation:** LocalModels.score in [models.py](../src/qrag/models.py).

For nonzero vectors a and b, cosine similarity is:

$$
\cos(a,b)=\frac{a^\top b}{\|a\|_2\|b\|_2}.
$$

Define normalized vectors u = a / ||a||₂ and v = b / ||b||₂. Their norms are one, giving:

$$
\cos(a,b)=u^\top v.
$$

Normalization removes vector magnitude from this score. It does not calibrate the result as a probability. A score of 0.8 does not mean an 80 percent probability that a passage answers the question.

The encoder is called with normalize_embeddings enabled, producing one question vector and one vector per passage. See [SentenceTransformer encoding](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).

Stack the normalized passage vectors as rows of D:

$$
D\in\mathbb R^{n\times d},\quad u\in\mathbb R^d,\quad
r=Du\in\mathbb R^n,\quad G=DD^\top\in\mathbb R^{n\times n}.
$$

| Quantity | Meaning | Shape for ten candidates |
| --- | --- | --- |
| Encoded batch | Question followed by candidate vectors | 11 × 384 |
| u | Question embedding | 384 |
| D | Passage embeddings | 10 × 384 |
| r | Relevance scores | 10 |
| G | Raw passage cosine matrix | 10 × 10 |
| S | Elementwise max of G and zero | 10 × 10 |

S is a redundancy proxy. Negative cosine values are clipped so the current model does not reward selecting a pair simply because its embeddings are opposed. The optimizer ignores diagonal entries: a passage must not incur a pair penalty with itself.

Computing all passage-pair similarities costs roughly O(n²d) arithmetic and O(n²) storage. This is reasonable for small candidate pools but motivates retrieval before pairwise scoring on a large corpus. A vector index accelerates candidate search; it is not the same object as the pair matrix.

## The selection objective and its interpretation

**Implementation:** build_problem and SelectionProblem.energy in [optimization.py](../src/qrag/optimization.py).

Let xᵢ indicate selection of passage i. The implemented problem is:

$$
\min_{x\in\{0,1\}^{n}}
E(x)=-\alpha\sum_i r_i x_i+\beta\sum_{i<j}S_{ij}x_i x_j,
\qquad \sum_i x_i=k.
$$

The negative sign turns a relevance reward into a minimization term. The positive pair term charges for selecting similar passages together. α and β control the tradeoff.

The code stores the linear coefficients aᵢ = −αrᵢ and a strict upper-triangular matrix B with Bᵢⱼ = βSᵢⱼ for i < j:

$$
E(x)=a^\top x+x^\top Bx.
$$

Using both off-diagonal triangles with the same coefficient would double-count every pair. The SelectionProblem constructor rejects a nonzero lower triangle or diagonal. It also checks dimensions, finite coefficients and the count bound, and copies arrays before making them read-only.

The cardinality constraint matters. Without it, the optimizer may improve recall by passing more documents to generation. Equal count controls that effect but does not ensure equal tokens or equal evidence.

With α > 0, dividing the objective by α shows that the relative preference depends on β/α. Absolute scaling still matters for some numerical algorithms and for comparisons with constraint penalties. These weights do not become universally optimal because one development run used them.

### A fully worked geometrically valid example

The following two-dimensional vectors are illustrative, not measured MiniLM outputs. Each has unit norm:

$$
u=(1,0),\quad
v_A=(0.8,0.6),\quad
v_B=(0.6,0.8),\quad
v_C=(0.6,-0.8).
$$

Then:

$$
r=(0.8,0.6,0.6),\qquad
G=\begin{bmatrix}
1&0.96&0\\
0.96&1&-0.28\\
0&-0.28&1
\end{bmatrix}.
$$

Clipping negatives gives S_AB = 0.96, S_AC = 0 and S_BC = 0. Take α = 1, β = 0.5 and k = 2. These example weights differ from the real smoke configuration.

| Selected pair | Negative relevance | Redundancy penalty | Total energy |
| --- | ---: | ---: | ---: |
| A and B | −1.40 | 0.48 | −0.92 |
| A and C | −1.40 | 0.00 | −1.40 |
| B and C | −1.20 | 0.00 | −1.20 |

Stable relevance ranking chooses A and B because B and C tie and B appears earlier. The full objective prefers A and C, avoiding the near-duplicate pair.

~~~python
import numpy as np
from qrag.optimization import build_problem, select_milp, select_top_k

u = np.array([1.0, 0.0])
D = np.array([[0.8, 0.6], [0.6, 0.8], [0.6, -0.8]])
relevance = D @ u
problem = build_problem(relevance, D @ D.T, k=2, alpha=1.0, beta=0.5)
ranking = select_top_k(problem, relevance)
optimized = select_milp(problem)
# ranking.indices == (0, 1), energy approximately -0.92
# optimized.indices == (0, 2), energy approximately -1.40
~~~

This example was checked against the current MILP and exhaustive oracle. It demonstrates the objective's behavior, not that A and C would produce a better real answer.

### Scoring and solving are different responsibilities

Scoring defines which selections are preferred. A solver searches for a good selection under that definition.

Ranking exactly maximizes individual relevance at fixed k; it is not trying to solve the relevance–redundancy objective. MILP targets that full objective. Thus a ranking-versus-MILP comparison changes the selection policy. A MILP-versus-QAOA solver comparison must keep the full objective and feasible set fixed.

A bad objective can be solved perfectly. Conversely, a worse-energy selection can generate a better answer because energy is only a proxy for downstream quality. Such a result does not on its own establish a quantum benefit.

## From binary quadratic optimization to MILP

ILP means integer linear programming. MILP means mixed integer linear programming, with some continuous variables alongside integer ones. Both use linear objectives and constraints; the integer requirement makes the problem substantially different from unconstrained calculus.

### Why auxiliary variables work

Introduce yᵢⱼ for xᵢxⱼ and impose:

$$
0\le y_{ij}\le1,\quad
y_{ij}\le x_i,\quad
y_{ij}\le x_j,\quad
y_{ij}\ge x_i+x_j-1.
$$

The resulting linear objective is:

$$
\min -\alpha\sum_i r_i x_i+\sum_{i<j}\beta S_{ij}y_{ij},
\qquad \sum_i x_i=k.
$$

| xᵢ | xⱼ | Forced lower bound on y | Forced upper bound on y | y |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 | 1 |

Therefore y need not be declared integer when x is binary. All inequalities are needed for a general objective with signed pair coefficients. If only upper bounds were used, a minimizer could wrongly choose y = 0 for a selected pair with positive cost. If only lower bounds were used, a negative pair coefficient could incentivize y = 1 for an absent pair.

### The continuous relaxation

A solver can temporarily relax x to [0,1] when computing bounds. With xᵢ = xⱼ = 0.5, the same inequalities permit:

$$
0\le y_{ij}\le0.5.
$$

The actual product is 0.25, but the relaxation does not force that value. This does not invalidate the integer formulation. The relaxed feasible set contains the integer feasible set, so minimizing over it supplies a lower bound on the integer optimum.

### Bounds and search

An incumbent is the best known feasible integer selection. Let U be its energy and L a valid lower bound:

$$
L\le E^\star\le U,\qquad
0\le U-E^\star\le U-L.
$$

For example, L = −12 and U = −9 leaves an absolute uncertainty of at most 3. Negative energies make naive quality ratios awkward; absolute gaps are easier to interpret.

Branch-and-bound uses relaxations and branching to eliminate regions that cannot improve the incumbent. It can avoid enumerating every bitstring, although difficult integer problems still have exponential worst-case behavior.

The [SciPy interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html) distinguishes optimal, limited, infeasible, unbounded and error outcomes. The current wrapper requests zero relative gap, validates the returned binary selection and records bounds/status. Optimality remains subject to solver numerical tolerances; it is not infinite-precision proof.

### Mapping to the actual implementation

select_milp creates n binary x variables plus one continuous y for each nonzero upper-triangular coefficient. If there are m retained interactions, it creates n + m variables and 1 + 3m linear rows. The first row enforces exact count. Each pair contributes:

$$
y_{ij}-x_i\le0,\quad
y_{ij}-x_j\le0,\quad
y_{ij}-x_i-x_j\ge-1.
$$

The matrix is stored sparsely. All variable bounds are [0,1]; only the first n integrality entries are enabled. The returned x values are checked for near-integrality before IDs are mapped back to source passages.

The exhaustive oracle enumerates combinations with exactly k selections, limited to n ≤ 20 in this implementation. There are binomial(n,k) such selections, including 252 for n = 10 and k = 5. This oracle validates the formulation rather than replacing scalable optimization.

**Transferable application:** selecting projects under a budget, facility placement and scheduling all require separating objective design, constraints and solver guarantees in the same way.

## Answer generation and inference behavior

**Implementation:** LocalModels.prepare and LocalModels.generate in [models.py](../src/qrag/models.py).

The generator is a pretrained causal language model. Given prompt P and generated answer tokens a₁ through aₜ, autoregressive generation models:

$$
p(a_1,\ldots,a_T\mid P)=\prod_{t=1}^{T}p(a_t\mid P,a_{<t}).
$$

The current call disables sampling. Greedy decoding chooses a highest-probability next token at each step; it does not guarantee the globally most probable complete answer. See [generation strategies](https://huggingface.co/docs/transformers/main/en/generation_strategies).

### Prompt construction and context order

Each selected source is formatted with its ID, title and text. A system message asks for a short answer using only these sources and specifies noanswer when evidence is insufficient. A user message contains the sources and question. The tokenizer's chat template adds the model's expected message delimiters.

The template is rendered first, then tokenized with add_special_tokens disabled to avoid adding another set of special tokens. Both selectors use the same template and source-formatting policy.

Selected indices are sorted into original candidate order before generation. This controls one source of variation: two methods choosing the same set should not receive different source orders. Stable ranking breaks equal-score ties using input order.

The source-only instruction is a behavioral request, not a security proof. The model may use memorized knowledge, follow malicious source instructions or hallucinate. Recording supplied sources does not establish that the answer causally depends on them. The current prompt requests no generated citations; evidence IDs in artifacts describe supplied context.

### Token budgets and explicit failure

Let T_prompt be the tokenized chat prompt and T_new the reserved generated-token allowance. The adapter checks:

$$
T_{\mathrm{prompt}}+T_{\mathrm{new}}
\le \min(B_{\mathrm{config}},B_{\mathrm{model}}).
$$

For the current run, the effective total limit is 4,096 and T_new is 32, so the prompt must fit within 4,064 tokens. A 4,080-token prompt fails this check even if the model might have stopped early.

context_tokens counts the separately tokenized source block. input_tokens counts the complete rendered prompt. Their difference includes instructions, question and formatting; it is not generally constant across questions. Independently measured context-token counts are not guaranteed additive across arbitrary tokenizer boundaries.

max_new_tokens is an upper bound, not a fixed answer length. hit_output_limit flags a response reaching it; that flag indicates possible truncation, not proof that every such answer is incomplete.

### Loading and computation

Model snapshots are resolved at immutable revisions. The example configuration uses local-only resolution, CPU, float32 generator weights and four PyTorch threads. prepare loads models once per invocation. score reuses the embedder; generate reuses the language model.

Evaluation mode and inference_mode avoid training behavior and gradient bookkeeping. No backpropagation updates occur. Disabling sampling improves repeatability under a fixed environment, but floating-point operations, hardware and dependencies can still produce differences.

The legacy classes use lazy loading: weights are loaded when first needed. The new runner explicitly calls prepare before processing questions, making startup time visible. Both approaches can reuse a loaded model; loading on every question would waste work.

Batching groups multiple inputs into a model operation. The embedding adapter uses batches of up to 32 texts. Larger batches may improve throughput but consume more memory, especially with long padded sequences. The generation adapter currently handles one selected context at a time; it is not a continuously batched inference server.

Cold model startup, model-ready inference and cached-embedding execution are different conditions. The current run loads models at invocation start and recomputes document embeddings. A cached model file on disk is not the same as a loaded model or a cached document embedding.

## Evaluation with worked calculations

**Implementation:** [metrics.py](../src/qrag/metrics.py), with aggregation in [run.py](../src/qrag/experiments/run.py).

### Answer normalization and exact match

Normalization lowercases, removes ASCII punctuation and English articles, then collapses whitespace. Thus The United States. and United States normalize to the same string. Exact match is one when normalized prediction and reference are equal and zero otherwise.

The implementation follows [HotpotQA's reference semantics](https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py), including special yes/no/noanswer handling and the zero-overlap convention.

### Token F1 and repeated words

Let c_p(w) and c_g(w) count token w in prediction and reference. Multiset overlap is:

$$
m=\sum_w\min(c_p(w),c_g(w)).
$$

Then:

$$
P=\frac{m}{N_p},\quad R=\frac{m}{N_g},\quad
F_1=\frac{2PR}{P+R},
$$

with zero assigned when no overlap exists. Special-answer cases are handled before general overlap scoring.

For prediction red red blue and reference red blue blue, m = 2, N_p = N_g = 3 and F1 = 2/3. Using sets would incorrectly discard repetition.

For prediction India and Nepal versus reference India, m = 1, P = 1/3, R = 1 and F1 = 1/2. A longer answer can contain the correct token while receiving a precision penalty.

Under the implemented reference rules, empty-normalized strings match exactly but have zero token F1. yes indeed against yes receives zero F1 because a special gold answer must match exactly after normalization.

### Document evidence metrics

Let D be selected titles and G annotated supporting titles. Document precision is |D∩G|/|D|; recall is |D∩G|/|G|. Complete support is one exactly when G is a subset of D.

If two documents are annotated and five are selected, selecting both gives precision 2/5, recall 1 and complete support 1. Selecting one gives precision 1/5, recall 1/2 and complete support 0.

These labels identify annotated support, not every possible valid evidence route. Missing support annotations produce null document metrics. The runner does not predict supporting sentences, so these figures are not official sentence-level supporting-fact F1.

### Aggregation and failures

The runner averages per-question answer F1. It does not pool tokens across the whole dataset or compute F1 from averaged precision/recall.

For example, questions with (P,R) equal to (1,1/2) and (1/2,1) each have F1 = 2/3. Their mean F1 is 2/3, whereas F1 calculated from mean P = mean R = 3/4 is 3/4. These are different aggregations.

All-question answer averages count failed method executions as zero. If one of three questions succeeds correctly and two fail, EM is 1/3, not 1. Evidence, token and generation summaries currently use successful records only and say so in their field names. Failure counts must accompany them.

### What the three-question result means

The recorded baseline has answer EM/F1 of 1/3 for both methods. MILP obtains higher annotated document recall but does not improve that answer metric. Equal passage count still permits unequal token counts.

Romanticism versus Romantic is a semantic near-match with zero exact token overlap. Another example asks for a film but has a person as its reference. Preserve the original primary score and record these cases; changing labels or metrics after viewing which method wins compromises the comparison.

These observations motivate error analysis. They do not justify a general ranking of methods. Future paired confidence intervals should resample questions together across methods; repeated solver seeds for one question are not independent new questions.

## Reproducibility and software contracts

### Configuration and package installation

[config.py](../src/qrag/config.py) loads TOML into ExperimentConfig and rejects unknown keys. __post_init__ checks types, numeric ranges, finite weights, device choices and immutable model revisions. Explicit type checks prevent boolean values from accidentally serving as positive integers.

The package configuration in [pyproject.toml](../pyproject.toml) makes qrag importable. An editable installation points imports at the source tree. Installing the package does not download model weights.

[requirements-baselines.lock](../requirements-baselines.lock) pins the tested NumPy/SciPy pair. The broader model stack is recorded per run but not supplied as a portable full-environment lock. Model snapshot revisions identify weights/configuration; package pins identify software. Both matter. [pip documentation](https://pip.pypa.io/en/stable/topics/repeatable-installs/)

### Manifest versus configuration

A configuration states what is requested. A manifest records that configuration together with dataset/source identities, actual backend, package versions, selected question IDs, preparation and execution details.

The runner seeds Python, NumPy and PyTorch in the real backend. Seeds do not repair dataset leakage, ensure correct metrics or guarantee identical floating-point results on every platform.

SHA-256 maps file bytes to an identifying digest. A changed dataset produces a different expected identity even if the filename stays the same. The package source hash covers qrag Python files; it does not archive those files or every external dependency. Git metadata and model revisions add context but are not substitutes for preserving source and data.

### Atomic files and resume

[artifacts.py](../src/qrag/experiments/artifacts.py) writes a temporary file in the target directory, flushes it, calls fsync and replaces the destination. This reduces the risk of a visibly half-written JSON artifact. It is not a multi-file database transaction, concurrent-writer protocol or complete guarantee against every power-loss scenario.

RunStore keys each prediction by question ID and method. Duplicate keys are rejected. Resume checks configuration, dataset, question IDs, source, environment and backend identity before reusing records.

Current behavior skips all completed records, including error records. It does not automatically retry failed predictions. A corrected run needs a new directory. A fully completed resume can recreate the summary without loading model weights.

Per-method failures after startup are recorded and retained in the answer denominator. Exceptions during model preparation produce failure artifacts after the store exists. Configuration, dataset loading or snapshot-resolution errors occurring before store creation may only produce a CLI error. This is an implementation boundary, not an assurance that every failure has a manifest.

### Tests and their limits

The seventeen test methods cover adapter boundaries, configuration errors, metric edge cases, MILP/exhaustive agreement, signed pairs, solver limits and resume/failure behavior. Several methods contain multiple cases.

Offline tests use an explicitly labeled fake model backend. They verify orchestration, not language-model quality. The separate real MiniLM/Qwen run verifies the integrated inference path on three development examples.

The CI workflow exists in [.github/workflows/baselines.yml](../.github/workflows/baselines.yml). Its presence does not establish that a remote GitHub Actions run has completed. It installs the core and runs offline tests without fetching models.

## A complete trace through the actual first question

This section uses baseline_dev_001 rather than the illustrative vectors. The question asks who was the body double for Emilia Clarke's Daenerys character; the reference is Rosie Mac. Its ID is 5abed9f45542994516f4545a.

1. load_examples adapts the JSON into a QueryInput with ten candidates and separate EvaluationLabels.
2. LocalModels.score encodes eleven texts: the question and ten candidate passages. It produces r with shape (10,) and similarities with shape (10,10).
3. build_problem applies α = 1 and β = 0.2, stores the strict upper triangle and requires exactly five selections.
4. Top-k selects candidate indices 0, 2, 5, 6 and 7. MILP selects 1, 4, 5, 6 and 7. Indices are zero-based and map through the original candidate tuple.
5. Both contexts are ordered by those original indices, formatted with source IDs and passed through the same chat-template policy.
6. Both methods generate Rosie Mac. Only after generation are references used for scoring.
7. save_record preserves the answer, selected IDs, energy, status, tokens, prompt and metrics. summarize aggregates completed records.

| Recorded quantity | Top k | MILP |
| --- | ---: | ---: |
| Selected count | 5 | 5 |
| Full energy | −1.31719957 | −1.84270207 |
| Context tokens | 655 | 754 |
| Full input tokens | 736 | 835 |
| Answer EM and F1 | 1 and 1 | 1 and 1 |
| Solver optimum certified | Not claimed by ranking | Yes for this objective |

The energy difference establishes a better value under this objective. This question does not exhibit an answer improvement because both answers match. The token counts demonstrate why fixed-count and token-budget studies are separate.

All values trace to the [evidence snapshot](research_report/evidence/baseline_dev_001.json) and the full local run directory. The actual model experiment occurred on November 4; documentation checks do not create new model results.

## Foundations for the planned graph and quantum work

**Status:** the following concepts explain planned extensions and the legacy wrapper. They are not features of the new baseline experiment.

### Graph features and complementarity

An entity/relation graph might contain Film A → directed by → Maya Rao and Maya Rao → born in → Jaipur. Its edges need source provenance. An entity-link graph based only on shared mentions is a simpler structure and must not be described as verified semantic relations.

The optimizer instead uses a graph whose nodes are passages and whose edges are pair interactions. Features from the first graph may determine coefficients in the second:

$$
E_{\mathrm{graph}}(x)
=-\alpha\sum_i r_i x_i
+\sum_{i<j}(\beta S_{ij}-\eta C_{ij})x_i x_j.
$$

Cᵢⱼ estimates complementarity; η controls its weight. Shared entities alone are insufficient to establish it. Aliases, extraction mistakes and irrelevant paths can create misleading connections. Coefficients must come from allowed question/text inputs and development-frozen rules.

Graph features are a scoring change. Evaluating them classically first isolates whether they improve the model of useful evidence before circuit behavior complicates interpretation.

### QUBO and Ising mapping

For a binary energy with strict upper-triangular pair coefficients:

$$
E(x)=\sum_i a_i x_i+\sum_{i<j}b_{ij}x_i x_j,
\qquad x_i=\frac{I-Z_i}{2}.
$$

Z has eigenvalue +1 on bit 0 and −1 on bit 1. Substitution yields:

$$
H_C=cI+\sum_i h_i Z_i+\sum_{i<j}J_{ij}Z_i Z_j,
$$

$$
c=\frac12\sum_i a_i+\frac14\sum_{i<j}b_{ij},
\qquad J_{ij}=\frac14 b_{ij},
$$

$$
h_i=-\frac12a_i
-\frac14\left(\sum_{j<i}b_{ji}+\sum_{j>i}b_{ij}\right).
$$

The constant does not change which bitstring minimizes energy, but it matters when comparing reported Hamiltonian energies with the original objective.

For a = (−1,−0.5) and b₁₂ = 0.2, c = −0.7, h = (0.45,0.2) and J₁₂ = 0.05. Substitution gives energies 0, −1, −0.5 and −1.3 for bits (0,0), (1,0), (0,1) and (1,1). These values were checked algebraically and numerically. They are illustrative mapping checks, not quantum execution results.

Before mapping a constrained selection problem, handle its constraints. One option adds λ(sum xᵢ − k)²:

$$
\lambda\left(\sum_i x_i-k\right)^2
=\lambda\left[(1-2k)\sum_i x_i
+2\sum_{i<j}x_i x_j+k^2\right].
$$

Every pair receives a penalty coupling. Removing semantic edges therefore need not make the complete circuit sparse. A cardinality-preserving mixer avoids this particular penalty formulation but introduces its own preparation and mixing costs.

### QAOA and classical parameter optimization

The standard variational structure alternates a cost Hamiltonian H_C and mixer H_M, following the [original QAOA formulation](https://arxiv.org/abs/1411.4028):

$$
|\psi_p\rangle=U_p\cdots U_1|\psi_0\rangle,\quad
U_\ell=e^{-i\theta_\ell H_M}e^{-i\varphi_\ell H_C}.
$$

The classical optimizer adjusts the angles to reduce the expected energy:

$$
\mathcal L(\varphi,\theta)=\langle\psi_p|H_C|\psi_p\rangle.
$$

For a fixed circuit, M measurement samples give an estimator:

$$
\widehat{\mathcal L}=\frac1M\sum_{s=1}^{M}E(x^{(s)}).
$$

Sampling uncertainty, optimizer behavior and physical noise are separate issues. Minimizing expectation is also different from guaranteeing that a finite sample contains the best feasible bitstring.

The [legacy wrapper](../src/optimization/qaoa_solver.py) uses StatevectorSampler, COBYLA and default p = 1 with a maximum-iteration setting of 50. Statevector sampling is classical simulation of quantum states, not quantum hardware. COBYLA adjusts circuit angles; it does not directly optimize LLM parameters. The [IBM QAOA tutorial](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm) provides the algorithmic reference.

COBYLA means Constrained Optimization BY Linear Approximation. It uses function evaluations and local linear models rather than requiring analytical derivatives. Here the function is a circuit-energy estimate and the parameters are angles. Its local search and finite evaluation budget do not certify the global optimum of the circuit-angle landscape. [COBYLA documentation](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html)

Increasing circuit depth does not guarantee better observed outcomes with a finite optimizer budget and noisy execution. Report shots, parameter evaluations, compilation, constraints and feasibility alongside answer quality.

### The legacy exact solver and Qiskit adapters

The earlier [exact solver](../src/optimization/exact_solver.py) wraps NumPyMinimumEigensolver, which computes a lowest eigenvalue/state classically. The operator for n binary decisions acts on a space of dimension 2ⁿ; implementations can exploit structure, but the method is not a general scalable substitute for MILP. [API reference](https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.NumPyMinimumEigensolver.html)

MinimumEigenOptimizer is the optimization adapter: it maps supported quadratic problems to an operator and interprets eigensolver output as optimization variables. Its name does not identify whether the underlying method uses quantum hardware. [Adapter reference](https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.algorithms.MinimumEigenOptimizer.html)

StatevectorSampler simulates state evolution and samples from the resulting distribution. Even with an ideal simulated state, finite samples introduce measurement-sampling variability. This is distinct from physical-device noise. [Sampler reference](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorSampler)

The new constrained MILP baseline uses none of these eigensolver wrappers. Its optimum is a classical reference for the specified objective, not a demonstrated output from a hypothetical perfect quantum computer.

### Sparsification changes the optimization problem

Let the sparse objective retain pair terms through a mask Mᵢⱼ:

$$
\widetilde E(x)=\sum_i a_i x_i+\sum_{i<j}M_{ij}b_{ij}x_i x_j.
$$

Both classical and quantum solvers must be evaluated against the original target as well as the surrogate. Otherwise a lower reported energy may merely reflect removal of costs.

Let δ be the sum of absolute removed coefficients. Because binary products lie in [0,1]:

$$
|E(x)-\widetilde E(x)|\le\delta.
$$

If both problems have the same feasible set and the sparse solution is ε-suboptimal under the sparse objective, then:

$$
E(\widetilde x)
\le\widetilde E(\widetilde x)+\delta
\le\widetilde E(x^\star)+\epsilon+\delta
\le E(x^\star)+\epsilon+2\delta.
$$

This elementary bound is a useful check, not a novelty claim or an answer-F1 guarantee. It depends on a valid ε and unchanged constraints.

Circuit resources must include state preparation, mixers, routing and constraint encoding. Sparsifying interactions generally does not reduce the number of candidate qubits. A statevector simulator stores amplitudes growing as 2ⁿ; raw complex128 storage alone is about 16 × 2ⁿ bytes, before additional simulator memory. Simulation behavior cannot establish practical hardware speedup.

## Upcoming engineering concepts and their status

The following designs are planned, not claims about the present runner.

| Concept | Purpose | Design issue to verify |
| --- | --- | --- |
| Embedding cache | Reuse unchanged representations | Include text/model/tokenizer/chunking/normalization identity and detect stale entries |
| Persistent index | Search a corpus without rebuilding per query | Keep vectors and metadata consistent across versions |
| Chunking | Represent long inputs within model limits | Preserve offsets, overlap and supporting-fact mappings |
| Token-budget selection | Bound actual generator context | Check the assembled prompt rather than only passage estimates |
| FastAPI service | Expose the common pipeline to clients | Validate requests, bound long jobs and label fallbacks |
| Observability | Attribute latency and failures | Separate model loading, cache behavior, selection and generation |

For example, caching document embeddings by filename alone is unsafe: content can change without a rename. Caching by content alone is also insufficient when the embedding model changes. A correct cache entry represents a computation identity.

[FAISS](https://faiss.ai/) is a library for vector similarity search and clustering. It would supply the planned corpus index, while the current supplied-pool baseline directly computes its small score matrices. Exact search avoids approximation error during initial selector comparisons; approximate indexes can later trade retrieval accuracy for resources. Installing FAISS alone does not mean that persistent corpus retrieval exists.

An API makes the pipeline accessible; it does not improve its scientific quality. A classical fallback can improve service reliability but must not be silently counted as a successful QAOA experiment.

## Technical review questions and reasoning checks

1. Why does a normalized dot product equal cosine similarity, and why is it not a relevance probability?
2. Why must the pair matrix use one triangle, and what happens if both triangles are populated?
3. Which linearization inequalities prevent incorrect y values with positive versus negative pair costs?
4. With fractional xᵢ = xⱼ = 0.5, why is y allowed to differ from 0.25?
5. Can an exact solver yield worse answers than an approximate solver? What would that establish?
6. What changes when five short passages are compared with five long passages?
7. Which information distinguishes a reproducible manifest from a configuration file?
8. Why are successful-only latency averages insufficient without failure counts?
9. Why can a sparse semantic graph yield a dense quantum circuit?
10. What must remain fixed to attribute a gain to the quantum solver rather than improved scoring?

Reasoning checks: normalization makes norms one; matrix symmetry otherwise double-counts pairs; upper and lower product bounds serve different signed costs; the continuous relaxation is a superset of valid integer points; task quality and proxy optimality differ; document count does not control tokens; manifests include actual data/source/runtime identities; failures can hide expensive or difficult cases; penalties and compilation add interactions; solver comparisons require common objectives, feasible sets, features and evaluation settings.

Receiving these explanations does not establish independent understanding. Practical checks should include recalculating the numerical example, predicting a constraint change and interpreting a saved record without relying on the aggregate table.

## Sources and implementation references

Primary sources support the transformer, generation, optimization and quantum background. The inspected project source is authoritative for what this version actually implements. Documentation versions can differ from the recorded runtime; no dependency upgrade was performed for these notes.

- [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Transformers generation strategies](https://huggingface.co/docs/transformers/main/en/generation_strategies)
- [SciPy MILP](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
- [IBM QAOA workflow](https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm)
- [Original QAOA paper](https://arxiv.org/abs/1411.4028)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [pip repeatable installations](https://pip.pypa.io/en/stable/topics/repeatable-installs/)
- [Official HotpotQA evaluator](https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py)

For project execution, use [Baseline guide](BASELINE_GUIDE.md). For completed versus remaining work, use [Development sequence](DEVELOPMENT_SEQUENCE.md) and the [implementation plan](IMPLEMENTATION_PLAN.md).

## Phase A foundations — what reproducibility establishes

An environment snapshot answers “which software was installed?” An execution check answers the different question “could these packages perform the needed calculation on this host?” A CUDA package can exist without a usable GPU. The environment script therefore multiplies tensors on the selected device, simulates a known Bell state, and solves a one-variable binary problem. For that problem, minimize -x with x in {0,1}: the two energies are 0 and -1, so the expected solution is x=1. The Bell state has probabilities (1/2,0,0,1/2), which provides a simple simulation check independent of the RAG application.

A fixed seed initializes a pseudorandom sequence. It does not fix every floating-point reduction, GPU kernel or future package implementation. A lock fixes package versions; a model revision fixes weights/tokenizer files; content hashes identify data and source bytes. Together these reduce ambiguity but do not establish that an experiment is correct. That requires mathematical checks and actual predictions.

For paired evaluation, let d_q be method A's answer F1 minus method B's on question q. The estimated difference is the sum of d_q divided by the number N of questions. Bootstrap resampling draws N question IDs with replacement, computes that mean again, and repeats. The 2.5th and 97.5th percentiles give a 95% percentile interval. Pairing preserves each question's difficulty across methods. Solver seeds are repeated computations on one question, not new independent questions; average them within question before resampling. An interval spanning zero permits effects in both directions and does not prove equality.

The full [protocol](EXPERIMENT_PROTOCOL.md) states the comparisons before final evaluation. This prevents choosing whichever metric, seed or subset looks most favorable afterward. Such a choice would change the question being tested and exaggerate apparent evidence.

## Phase B foundations — annotations, aliases and dataset-specific scoring

A source sentence is an original unit of text; its supporting label is a separate statement that this unit is relevant to the expected answer. Keeping original sentence indices permits us to map evidence through later chunking. If a label refers to sentence 9 in a three-sentence document, the mapping is invalid. Silently accepting it could report false evidence recall, so validation rejects it.

A title is a display name, not always a unique identifier. MuSiQue paragraphs with the same title must remain distinct. We therefore use stable candidate IDs for its supporting-paragraph metrics. Replacing paragraph identities with titles could incorrectly treat an unsupported paragraph as supporting evidence.

For answer tokens, let m be the multiset overlap, P the number of predicted tokens, and G the number of reference tokens. Precision is m/P, recall is m/G, and their harmonic mean simplifies to F1 = 2m/(P+G) when both lists are nonempty. For prediction “red red blue” and reference “red blue blue”, m=2, P=G=3, so precision, recall and F1 are all 2/3. Counting unique words instead would incorrectly return 1.

The normalization steps are lowercase, remove ASCII punctuation, remove English articles and collapse whitespace. These are evaluation conventions, not semantic equivalence. “Romantic” and “Romanticism” can receive zero token overlap despite related meaning. HotpotQA additionally blocks partial matches to yes/no/noanswer and assigns F1=0 when normalized token overlap is empty, including two empty strings. MuSiQue follows its own scorer: two empty token lists have F1=1, and it takes the maximum score over valid answer aliases. Exact match and F1 maxima are computed separately. The adapter must not silently reuse HotpotQA's special rules for MuSiQue.

A held-out split is a set excluded from parameter decisions. Choosing IDs with a fixed shuffle and freezing their hashes makes later changes visible. We also compare normalized questions and word-trigram sets. For sets A and B, Jaccard similarity is |A intersection B| / |A union B|. A threshold of 0.8 flags highly overlapping questions, but paraphrases with different words may escape it. This is a useful audit, not proof of independence or absence of pretraining exposure.

Empty-context generation measures what the generator can do without supplied evidence. A gold-evidence oracle gives annotated sources to the generator as an explicitly labeled diagnostic. It uses labels and therefore must never be presented as ordinary inference. Poor oracle answers suggest generation, formatting or annotation limitations; they do not prove that the selector is the only bottleneck. These diagnostics help interpret subsequent selection experiments.
