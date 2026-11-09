# Technical foundations and implementation notes

**Version 1.0 working edition | Updated November 10 2026**

This companion explains the mathematics, ML concepts and engineering decisions behind the implemented research pipeline. It connects definitions to source functions, derives equations and provides numerical examples. [Research progress](RESEARCH_PROGRESS_REPORT.md) contains the experimental account; [Development sequence](DEVELOPMENT_SEQUENCE.md) records implementation order and decisions.

The implemented pipeline now includes token-safe chunking, embedding and graph caches, persistent exact corpus search, lexical/dense/reranking baselines, count/token constraints, MILP and heuristic selection, entity-link features, sparsification, QAOA simulation, two generators, answer evaluation and a separate local API. The early worked baseline remains useful for understanding the equations; phase-specific sections explain the later extensions. Typed factual relation extraction, physical quantum execution and quantum token-budget circuits are not implemented. Final evaluation and artifact assembly are currently running.

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

This diagram starts at a supplied candidate pool. The separate corpus mode first searches a persistent, deduplicated union of benchmark passages using exact FAISS search and BM25 rank fusion. Both modes then use the same selection/generation library. This is a bounded corpus experiment, not an unrestricted web or full-Wikipedia search.

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

The adapters validate required fields, stable IDs and annotation mappings. Documents preserve available source sentence strings; chunks preserve exact character offsets and sentence IDs. MuSiQue support uses paragraph IDs rather than assuming every title is unique. Frozen splits have exact normalized-question and token-trigram duplicate audits; these do not rule out every semantic paraphrase or shared source.

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

**Implementation:** the historical whole-passage LocalModels.score is in [models.py](../src/qrag/models.py). The main study uses ChunkEncoder.score in [retrieval.py](../src/qrag/retrieval.py), which aggregates token-safe chunks into one unit vector per document before computing the same r and S shapes below.

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

Cold model startup, model-ready inference and cached-embedding execution are different conditions. The historical first run recomputed passage embeddings. The main study reuses content-addressed query/document embeddings, and the service loads models lazily on its first job. A cached weight file on disk is not the same as a loaded model or a cached document embedding.

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

[requirements-baselines.lock](../requirements-baselines.lock) pins the small historical core. [requirements-laptop.lock](../requirements-laptop.lock) records the tested laptop environment, including transitive packages, while [requirements-ci.txt](../requirements-ci.txt) pins the lighter CI environment. The CUDA laptop snapshot is host-specific, not a guarantee of portable installation on every platform. Model snapshot revisions identify weights/configuration; package pins identify software. Both matter. [pip documentation](https://pip.pypa.io/en/stable/topics/repeatable-installs/)

### Manifest versus configuration

A configuration states what is requested. A manifest records that configuration together with dataset/source identities, actual backend, package versions, selected question IDs, preparation and execution details.

The runner seeds Python, NumPy and PyTorch in the real backend. Seeds do not repair dataset leakage, ensure correct metrics or guarantee identical floating-point results on every platform.

SHA-256 maps file bytes to an identifying digest. A changed dataset produces a different expected identity even if the filename stays the same. The package source hash covers qrag Python files. Main-study outputs also save their exact source snapshot; the hash alone would not archive the bytes or external dependencies. Git metadata and model revisions add context but are not substitutes for preserving source and data.

### Atomic files and resume

[artifacts.py](../src/qrag/experiments/artifacts.py) writes a temporary file in the target directory, flushes it, calls fsync and replaces the destination. This reduces the risk of a visibly half-written JSON artifact. It is not a multi-file database transaction, concurrent-writer protocol or complete guarantee against every power-loss scenario.

RunStore keys each prediction by question ID and method. Duplicate keys are rejected. Resume checks configuration, dataset, question IDs, source, environment and backend identity before reusing records.

The historical RunStore skips recorded successes and errors. The later study runner uses JournalRunStore in [journal.py](../src/qrag/experiments/journal.py): it appends and fsyncs each record, protects successful keys, records explicit attempts for retried errors, and saves a torn final line before recovery. Resume checks scientific identity first. Final reporting takes the latest attempt for each key; the append history remains inspectable. Runs have one writer; this journal is not a distributed database or a multiwriter locking protocol.

Per-method failures after startup are recorded and retained in the answer denominator. Exceptions during model preparation produce failure artifacts after the store exists. Configuration, dataset loading or snapshot-resolution errors occurring before store creation may only produce a CLI error. This is an implementation boundary, not an assurance that every failure has a manifest.

### Tests and their limits

The first seventeen tests covered the baseline. The expanded suite has 45 tests covering data, caches/indexes, provenance, signed MILP, budgets, quantum spectra and mixers, sparsification, statistics, journaling and service behavior. Several methods contain multiple cases.

Offline tests use an explicitly labeled fake model backend. They verify orchestration, not language-model quality. The separate real MiniLM/Qwen run verifies the integrated inference path on three development examples.

The baseline workflow and the expanded [research workflow](../.github/workflows/research.yml) have completed successfully on GitHub Actions. These checks do not download model weights or reproduce full scientific inference; local real-model runs provide that separate evidence. Container and wheel checks exercise packaging as well as Python tests.

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

**Reading order:** these are the introductory derivations originally written before the quantum implementation. The implemented versions, actual settings, limitations and checks are detailed in the Phase D–F sections below. The historical three-question baseline did not execute QAOA.

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

The table summarizes engineering requirements that are now implemented in the main study or service. Detailed mechanisms and measurements follow in the phase sections.

| Concept | Purpose | Design issue to verify |
| --- | --- | --- |
| Embedding cache | Reuse unchanged representations | Include text/model/tokenizer/chunking/normalization identity and detect stale entries |
| Persistent index | Search a corpus without rebuilding per query | Keep vectors and metadata consistent across versions |
| Chunking | Represent long inputs within model limits | Preserve offsets, overlap and supporting-fact mappings |
| Token-budget selection | Bound actual generator context | Check the assembled prompt rather than only passage estimates |
| FastAPI service | Expose the common pipeline to clients | Validate requests, bound long jobs and label fallbacks |
| Observability | Attribute latency and failures | Separate model loading, cache behavior, selection and generation |

For example, caching document embeddings by filename alone is unsafe: content can change without a rename. Caching by content alone is also insufficient when the embedding model changes. A correct cache entry represents a computation identity.

[FAISS](https://faiss.ai/) is a library for vector similarity search and clustering. The implemented corpus mode uses IndexFlatIP over unit chunk vectors, with checked SQLite metadata and file hashes. Supplied-pool experiments directly compute their small score matrices. Exact search avoids approximation error during these selector comparisons; approximate indexes could later trade retrieval accuracy for resources.

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

## Phase C foundations — chunking, caches, ranking and indexes

A tokenizer turns text into token IDs. Character length does not determine token length: punctuation and unusual words may require multiple tokens. We count tokens with the actual embedding tokenizer, including special tokens and the title prefix. The target is at most 240 tokens, below MiniLM's 256-token limit. A long sentence is divided using tokenizer character offsets; overlap retains local context around boundaries. Every resulting chunk points to an exact substring of its original document. Supporting sentence IDs are attached by overlap with that substring, not inferred from answers.

Let z_1 through z_m be a document's unit chunk vectors. Compute their arithmetic mean v_bar=(z_1+...+z_m)/m, then normalize v=v_bar/||v_bar||. The question's unit vector u gives document relevance u dot v. This includes representations of later text that the old truncated input omitted. It does not equal embedding the whole long passage with a hypothetical unlimited-context encoder, and mean pooling can dilute a small important fact. That is a representation choice to evaluate, not a guarantee of improvement. Overlapping windows can give boundary regions more weight.

The cache key hashes both content and the representation recipe. The recipe includes immutable model revision, chunk policy, title handling, target length, normalization, numeric storage and aggregation. A different recipe gets a different namespace even if the text is unchanged. A query has its own namespace. Cache values store vector length and a checksum of float32 bytes. A checksum mismatch raises an error; it is not interpreted as a valid zero vector. Hashes identify bytes and recipes, not semantic truth.

A vector index stores vectors for searching; a cache stores the result of computing a vector. They solve different problems. The exact FAISS index computes inner products against stored unit vectors. For unit vectors, inner product equals cosine similarity. SQLite stores each vector position's chunk ID and provenance. The index and metadata are one versioned bundle: mixing files from different builds can map a correct score to the wrong passage. Checksums and representation identities detect that mismatch. Exact search avoids approximate-neighbor error but costs roughly O(Nd) work for N stored vectors of dimension d per query.

BM25 is lexical retrieval. For each query term t, it combines an inverse-document-frequency weight with tf*(k1+1)/(tf+k1*(1-b+b*L/Lavg)), where tf is term frequency, L is document length, Lavg is average length, k1 controls frequency saturation, and b controls length normalization. The implementation uses rank-bm25's documented BM25Okapi convention. Lexical and dense scores have incompatible units. Reciprocal-rank fusion instead adds 1/(60+rank) from each ranking; rank begins at 1. This makes fusion depend on ranks rather than raw score scales. Stable sorting defines ties.

A cross-encoder reads the question and passage together and produces a scalar relevance score, not a calibrated probability that the passage contains a true answer. It is more expensive than comparing already stored dense vectors. We score token-safe chunks and use the maximum chunk score per document. This emphasizes a strong local match, whereas mean-pooled embeddings summarize chunks. Both are approximations; neither sees reference labels. Final candidate retrieval and downstream selection must be held constant when attributing effects to an optimizer.

The measured cache speedup covers an already-loaded embedding model and 50 development questions. It excludes generator loading, answer generation, graph construction and service overhead. Calling it a global “warm run” would hide which component was reused; the precise description is model-ready encoding with cache misses versus model-ready encoding with cache hits.

## Phase D foundations — budgets, heuristics and graph coefficients

### Native token constraints

Let t_i be a conservative estimate of the generator tokens needed to format passage i and T the available context budget. The linear constraint is sum(t_i*x_i) <= T. In count mode we instead impose sum(x_i)=k. These are different experiments: five short passages may use fewer tokens than two long ones. Variable-count mode also uses sum(x_i)>=1 so a nonempty feasible context is required. If no passage fits, the instance is infeasible and becomes a recorded failure rather than being silently changed.

For linear token costs, MILP needs no penalty or extra binary slack variables. It places the token row directly in the linear constraint matrix. The pair products still use y_ij<=x_i, y_ij<=x_j and y_ij>=x_i+x_j-1 with 0<=y_ij<=1. Negative pair coefficients are valid: the constraints enforce the product independently of coefficient sign. An inequality omitted merely because a coefficient is negative could change the feasible optimization problem.

Tokenizer lengths are not perfectly additive across concatenated strings. We estimate each formatted source separately and add a ten-token per-source margin, then independently count the actual complete context. This margin is an engineering guard, not a universal tokenizer theorem. If the exact count exceeds T, the run records a failure without trimming or claiming feasibility. The generator separately checks instructions, question, context and reserved output against its total input limit.

For example, costs (400,300,250) with T=600 permit passages 2 and 3 together (550), but do not permit 1 and 2 (700). Exact k=2 alone allows the latter; it controls a different resource. A method with the same token cap can still consume fewer actual tokens, so we report consumption as well as the cap.

### Classical policies

Relevance ranking sorts individual scores. Greedy energy selection repeatedly adds the feasible item with the largest reduction in the common energy. Its marginal gain for adding i to current set S is -a_i - sum of pair coefficients connecting i to S. This ignores future interactions, so it can miss a good pair whose individual members look weak. MILP searches the joint constrained problem and can certify optimality for its numerical model.

MMR balances relevance and similarity to what is already selected: 0.7*r_i - 0.3*max similarity(i,j) over selected j, with zero redundancy for an empty set. It is a selection policy, not an exact solver of our full quadratic objective. Greedy coverage uses a passage-by-question-term indicator matrix A. Current covered weight is the sum over terms of max A among selected passages. The next passage is chosen by added coverage plus a small relevance tie-break. These lexical requirements are observable query terms, not gold reasoning decompositions.

Simulated annealing starts from a feasible relevance selection. In fixed-count mode, swap one selected and one unselected item, preserving k. Token mode also considers add/drop moves but rejects any budget violation. An improving move is accepted; a worsening energy change delta is accepted with probability exp(-delta/temperature). Temperature falls geometrically over the recorded number of steps. The random seed fixes the proposed sequence under the same implementation. Annealing reports a heuristic result, never a global-optimum certificate.

### Entity-link graph and complementarity proxy

For each passage, extract exact candidate-title matches and capitalized spans, recording their character positions. Shared extracted entities induce links between passages. This makes two graphs distinct: the entity-link graph connects passage/mention evidence, while the optimization interaction graph carries numerical coefficients between binary passage choices. A text match is not an extracted true subject–predicate–object relation.

Let a_i be the fraction of non-stopword question terms appearing in passage i's title or text. Let L_ij be 1 when passages i and j share an extracted entity, otherwise 0. Define C_ij = L_ij * max(a_i,a_j) * sqrt(max(r_i,0)*max(r_j,0)). Each factor is nonnegative. The anchor lets a question-matching passage connect to a possible bridge; the square root downweights pairs with little dense relevance. The pair coefficient becomes b_ij = beta*max(similarity_ij,0) - gamma*C_ij. Positive b discourages joint selection; negative b rewards it. Gamma controls the strength of an uncertain graph signal, not a probability of truth.

For relevance (0.8,0.5), anchor maximum 0.6 and a link, C=0.6*sqrt(0.4), approximately 0.3795. If similarity is 0.4, beta=0.2 and gamma=0.8, then b=0.08-0.3036=-0.2236. A mistaken link therefore introduces a real reward for selecting both passages. This explains why mathematically optimal selection can worsen answers when the graph feature is noisy. The actual development graph result is negative; the example explains a possible mechanism, not a diagnosis of every failed question.

### Timing and generation reuse

When different selectors return exactly the same ordered source IDs for one question, their deterministic generation input is identical. The runner generates once and marks subsequent uses as reused. It records both the original generation duration and zero additional generation execution for reuse. Summing every copied duration would overestimate total work. End-to-end invocation time remains authoritative. Reusing generation does not make repeated selector records statistically independent observations.

## Phase E foundations — deriving the implemented quantum calculation

### From a binary decision to an Ising spin

The computational basis state of qubit i represents x_i=0 or 1. Pauli Z has eigenvalue +1 on 0 and -1 on 1, so x_i=(1-Z_i)/2. Substitute this into E=sum(a_i*x_i)+sum over i<j of b_ij*x_i*x_j. A linear term becomes a_i/2-a_i*Z_i/2. A pair becomes b_ij*(1-Z_i-Z_j+Z_i*Z_j)/4. Collect constants, one-qubit terms and two-qubit terms:

c = sum(a_i)/2 + sum(b_ij)/4;
h_i = -a_i/2 - sum of all b touching i divided by 4;
J_ij = b_ij/4.

Thus H=c*I+sum(h_i*Z_i)+sum(J_ij*Z_i*Z_j) has the same basis-state energies as the binary objective. A constant changes reported energies but only adds a global phase to state evolution, so the circuit can omit that phase while energy evaluation retains it. Tests compare every bitstring on small signed problems rather than checking only the apparent best solution.

Qiskit labels qubit 0 as the least significant bit. Integer state 1 therefore means x_0=1 and all other x_i=0. Reversing displayed bit strings without a fixed convention would choose the wrong passages. The energy table explicitly forms bit i as (state_index shifted right by i) AND 1.

### Enforcing exactly k

The penalty construction adds lambda*(sum(x_i)-k)^2. Because binary x_i squared equals x_i, expansion gives lambda*(1-2k)*sum(x_i)+2*lambda*sum over all i<j x_i*x_j+lambda*k^2. Every pair acquires a coupling, even if the original semantic interaction was removed. This is why objective sparsity alone does not establish circuit sparsity.

Let B=sum(abs(a_i))+sum(abs(b_ij)). Between any two bitstrings, the objective changes by at most B because each binary monomial changes by at most 1. Any infeasible integer count differs from k by at least 1, so its penalty is at least lambda. Choosing lambda=B+1 ensures that no infeasible bitstring has lower encoded energy than every feasible bitstring, provided a feasible bitstring exists. This statement concerns the global minimum; a shallow QAOA circuit can still measure infeasible strings frequently. Its finite optimization budget does not magically attain that minimum.

The alternative prepares a seeded basis state with exactly k ones using X gates and applies pairwise XY mixing. For a pair, XX+YY exchanges 01 and 10 while leaving their total number of ones unchanged. The product RXX(beta)*RYY(beta) equals exp(-i*beta*(XX+YY)/2), since XX and YY commute on that pair. A sequence along a ring therefore preserves the total count in an ideal circuit. It starts from a feasible basis state, not a uniform Dicke state; that affects expressivity at small depth. The ring order and initial indices are recorded. Noise can break count conservation in the implemented physical gate sequence.

### Cost evolution and angle optimization

One layer applies cost evolution then mixing. For cost fields h and couplings J, RZ(2*gamma*h/s) and RZZ(2*gamma*J/s) implement exp(-i*gamma*H/s) up to the omitted constant, where s is the recorded maximum absolute field/coupling or 1, whichever is largest. The factor 2 follows from RZ(theta)=exp(-i*theta*Z/2). Every layer has gamma and beta, giving 2p real parameters.

For angles theta, statevector simulation gives probabilities P_theta(x). The ideal training objective is sum_x P_theta(x)*E_encoded(x). COBYLA adjusts angles using function evaluations without analytical derivatives. The main pilot allows 64 evaluations and records their energies and optimizer termination. A separate shot-training diagnostic estimates the expectation by averaging sampled energies, adding sampling variation. Neither procedure certifies a globally optimal angle vector.

Final measurement draws 1,024 samples from the trained distribution. We count infeasible samples, do not repair them, and choose the lowest surrogate-energy feasible measured subset with deterministic index tie-breaking. This best-of-samples policy uses classical energy evaluation and must be included in the method description. It differs from reporting the mean sampled energy or drawing one answer context. Full target energies are evaluated independently when sparsification changes the training objective.

### Complete resources and noise

Count preparation, cost operations, mixer operations and routing together. An abstract RZZ is a two-qubit operation but its decomposition may need multiple native gates. A nonlocal interaction on a line may require SWAP/routing operations. We transpile the complete trained circuit to a common basis and record both depth and two-qubit gate count under synthetic all-to-all and line connectivity, with a fixed compilation seed and optimization level. These are comparable compiler outputs, not device calibration or runtime estimates.

The diagnostic noise model applies depolarization probability 0.01 to compiled CX gates and 0.001 to X/SX gates, only during final all-to-all sampling. A density-matrix simulator computes the mixed state. Training remains ideal. Noise can change measured bit counts even for a mathematically count-preserving mixer. The reported feasible fractions therefore distinguish ideal operator conservation from noisy execution. Queueing, physical calibration and real quantum execution are absent and cannot be inferred from simulator timing.

## Phase F foundations — exact edge budgets and what sparsification can prove

### The four rules

Take the nonzero upper-triangular interactions as unordered edges. If there are m edges and retained fraction f, keep floor(f*m) edges exactly. Absolute retention sorts by |b_ij|. Random retention uses a recorded seeded permutation. The degree rule ranks each edge in each endpoint's incident list, takes the smaller endpoint rank as its symmetric priority, then breaks ties by magnitude and indices until the same hard budget is filled. It is a degree-oriented heuristic, not a guaranteed degree-regular graph.

Evidence guidance ranks linked pairs by C_ij*sqrt(|b_ij|), protects at most ceil(budget/2) such edges, and fills remaining slots from the absolute ordering. When there are too many bridge candidates, only the highest-ranked fit. When none exist, the rule reduces to magnitude retention. Both positive and negative retained coefficients are unchanged. All linear relevance terms remain. The method can protect mistaken links; the graph's name is not a preservation guarantee.

### Step-by-step objective bound

Let R be the removed edge set and define delta as the sum over R of |b_ij|. For a binary vector, every x_i*x_j is either 0 or 1. Therefore the absolute value of the removed sum is at most the sum of absolute removed coefficients: |E_full(x)-E_sparse(x)| <= delta. This holds for any binary x, regardless of whether the coefficients are positive or negative.

Let x_star minimize the full objective over feasible set F, and let x_hat be within epsilon of the minimum sparse energy over that SAME F. First, E_full(x_hat) <= E_sparse(x_hat)+delta. Second, E_sparse(x_hat) <= E_sparse(x_star)+epsilon, because the sparse optimum is no worse than the sparse energy of x_star. Third, E_sparse(x_star) <= E_full(x_star)+delta. Combining gives E_full(x_hat)-E_full(x_star) <= 2*delta+epsilon.

The assumptions matter: budgets and candidates must match, epsilon concerns the sparse objective, and both energies use the same coefficient scale and offsets. This is an elementary sanity bound, not a new theorem. It can be loose and gives no guarantee about answer F1. A measured QAOA state is not known epsilon-optimal unless a separate exact solver/bound establishes epsilon.

### Why a random control matters for small quantum cases

With n candidates and exactly k selected, there are n!/(k!*(n-k)!) feasible subsets. For n=10,k=5, this is 252, much less than all 1,024 bitstrings. If independent uniform feasible draws are used, the probability of seeing one particular optimal subset at least once in S draws is 1-(1-1/252)^S. With S=1,024 this is about 98.3%. That calculation assumes uniform independent draws and one fixed optimum; QAOA draws generally follow a nonuniform distribution.

A best-of-1,024-shot quantum policy can therefore appear strong simply because many small-case candidates are tested. The uniform feasible-sampling comparator uses the same number of draws and objective evaluations, with a recorded seed. It is a stronger control than comparing QAOA only to one random subset. At larger n the feasible space grows, so this coverage explanation changes; the final scaling study must state sizes and budgets rather than generalize from ten candidates.

### Calibrating without reusing the test set

For each candidate gamma, compute development mean F1 separately on HotpotQA and MuSiQue, average those two means with equal weight, and choose the highest score; ties favor smaller gamma. The selected value is 0.2. Unequal candidate-pool sizes do not give MuSiQue extra weight under this rule. Development tuning makes those development estimates optimistic. Only the frozen held-out evaluation can test whether the choice transfers. The main edge fraction remains the predeclared 0.5, with 0.25/0.75 as secondary sensitivity settings.

### Durable progress and repeated seeds

Appending one JSON record and flushing it avoids rewriting a growing file after each result. Fsync asks the operating system to commit the write. A crash can still interrupt the final line. Resume checks the immutable identity first, retains incomplete tail bytes for audit, then recomputes that unfinished record. Error retries get incremented attempt numbers; successful records cannot be replaced. Analysis uses the latest validated attempt for each question/method.

Repeated seeds describe solver variability on one question. For a method with three seeds, average its three F1 values inside that question, counting failures as zero, then bootstrap question means. Treating those three seeds as three unrelated questions would inflate the apparent sample size. The confidence intervals describe sampling variation over the observed question population and do not account for unknown pretrained-model contamination or every modeling choice.

## Phase G preparation — bounded corpora and measuring memory

A supplied-pool experiment assumes candidate passages are already given. A corpus experiment first searches a shared collection. Here the collection is the deduplicated union of benchmark input passages, constructed without answer/support labels. This is a bounded closed-corpus setting. It includes source passages by construction and is easier to specify than open Wikipedia retrieval; its results must not be described as full-Wikipedia performance.

Exact chunk search gives similarities. A document's dense retrieval score is the maximum similarity of any of its chunks. Lexical BM25 scores the original title and text. Reciprocal-rank fusion combines these rankings, and the highest-ranked documents form the common pool. HotpotQA candidates are additionally deduplicated by title at retrieval time to avoid ambiguous title annotations. MuSiQue evaluation tracks canonical paragraph content IDs. The selector receives this frozen pool; changing the retriever would be a separate intervention.

Gold evidence can be missing from a retrieved pool. That is a retrieval failure to measure, not invalid data to delete. Original dataset adapters validate support mappings; retrieved-pool adapters permit external reference evidence so recall can correctly be zero. Candidate recall is an evaluation-only diagnostic and never enters graph construction or selection.

GPU peak allocated memory reports the maximum tensor memory observed by PyTorch since process initialization. Process peak RSS reports the largest resident host memory observed by Linux. Neither is free memory or total physical-device usage, and neither isolates one query unless the counter is reset around that query. These fields are high-water marks under the recorded execution, not invented service capacity promises.

### Unicode surface forms and canonical names

A canonical entity name is a key used to join mentions. A surface form is the exact original text at a character range. They are different objects. For example, Unicode case-insensitive matching may relate “İstanbul” to “istanbul”, while casefolding the dotted capital I introduces a combining dot. The lengths and bytes of the normalized strings need not match. Provenance therefore checks that source[start:end] equals the stored surface, and stores the canonical key separately. Normalizing text before locating spans can shift character positions; offsets must always refer to the original source string.

## Service foundations — requests, jobs and observability

An HTTP API is a contract through which clients request operations. FastAPI validates JSON against typed Pydantic schemas. Unknown answer/relevance fields are rejected rather than quietly entering inference. A valid request receives status 202 and a job ID: accepted does not mean completed. The client polls that ID until the job completes or reports a failure. Invalid input receives 422; a full bounded queue receives 429; readiness returns 503 while model weights are not ready. Health and readiness answer different operational questions.

The inference worker runs outside the HTTP event loop, so a long model call does not block every health request. There is one inference worker and at most four accepted outstanding jobs. This prevents unbounded memory growth and overlapping model calls on one GPU. An exclusive database lock rejects accidental second workers using the same store. SQLite transactions persist job state; after restart, abandoned queued/running jobs are marked interrupted instead of being falsely reported complete. Terminal job retention is bounded.

Concurrency means multiple requests can be in progress; parallelism means computations actually execute simultaneously. Increasing web workers can duplicate model weights and exhaust memory. The service therefore serializes inference while still allowing request validation and status polling. Chunk embedding batches many texts into one model operation; that is different from launching concurrent generator requests.

Deadlines are checked between bounded stages. Generation has an output-token bound, solvers have evaluation/time budgets and inputs have size limits. These are not preemptive hard wall-clock cancellation: an already running tensor operation is not forcibly killed. A deadline failure is recorded. A quantum selection failure may trigger a separately labeled MILP fallback if the request permits it. The requested and actual methods, reason and resource fields remain visible. Research evaluation never substitutes that service fallback into QAOA results.

A trace groups stage spans under one request. Spans measure preparation, embedding, graph construction, selection and generation; structured logs identify job completion/failure without logging source text. OpenTelemetry can export local console spans. Queue time is start minus acceptance time; service time is completion minus start; total latency includes both. The operational p50 is the median of retained completed jobs, while p95 is the value below approximately 95% of that measured population. Mixed ingestion/query jobs and cold starts must not be confused with a homogeneous warm-query latency target. No unmeasured service-level promise is made.

Persistent corpus ingestion stores a checked FAISS/SQLite bundle through the same library used in experiments. Query requests retrieve candidates, then use the common selector and generator. Corpus IDs are constrained to simple names rather than arbitrary filesystem paths. This service is a local demonstration; its inference inputs contain no reference answers.

## Sampling, state preparation and a weak depth-one circuit

### Why a global phase cannot change an answer sample

A computational basis state corresponds to one exact binary subset. Write it as |x0>. The cost Hamiltonian is diagonal: H_C|x0> = E(x0)|x0>. Exponentiating this relation gives:

$$
e^{-i\gamma H_C}|x_0\rangle=e^{-i\gamma E(x_0)}|x_0\rangle.
$$

The multiplier has magnitude one and applies to the entire state. Measurement uses squared magnitudes, so multiplying every amplitude by that same complex number changes no probability. Applying a later linear mixer U_M cannot recover an observable difference:

$$
U_M e^{-i\gamma H_C}|x_0\rangle=e^{-i\gamma E(x_0)}U_M|x_0\rangle.
$$

Consequently, the frozen basis-start p=1 XY circuit has probabilities that depend on its mixer angle beta and starting subset, but not its first cost angle gamma. This gamma is a circuit angle, distinct from the graph-weight gamma in the selection objective. At p=2, mixing has created a superposition before the second cost layer, so the second cost angle can matter. The first remains inactive. This is an expressivity limitation, not a claim that QAOA generally ignores its objective. The classical optimizer still evaluates the expected energy under the chosen objective and can choose a different beta when that objective changes.

This diagnosis is verified in [the preparation regression check](../tests/test_preparation_control.py) by changing the first cost angle while holding the mixer angle fixed and comparing every state probability. The test then inserts feasible preparation and verifies that changing the cost angle does change probabilities, while all probability mass remains at the required count.

### Preparing a feasible superposition

The exploratory extension in [prepared_qaoa_study.py](../scripts/prepared_qaoa_study.py) keeps the original seeded subset but first applies one XY ring sweep at fixed angle pi/4. Every paired RXX/RYY exchange preserves the number of ones. Starting with k ones therefore produces a superposition of states that still have k ones. This is generally neither a uniform superposition nor a Dicke state.

If preparation produces sum_x c_x|x>, the cost layer produces sum_x c_x exp(-i gamma E(x))|x>. Different energies now receive different phases. A subsequent mixer can turn those relative phases into changed measurement probabilities through interference. This is the mechanism missing from the original first layer.

Preparation is not free: its gates, routing and depth are included when compiling the complete circuit. The fixed angle is not selected by looking for a favorable held-out answer result. This control is explicitly exploratory because the diagnosis occurred after the primary matrix was frozen. Both original and prepared results are retained. It would be misleading to silently replace the weaker implementation and describe the new outcome as the original principal experiment.

Generic compiled gate counts are also not lower bounds. A compiler that recognizes a known basis state could remove diagonal operations that only add a global phase. We report the actual fixed compiler policy and this limitation. Sparse symbolic interactions do not alone establish a necessary hardware cost reduction.

### How repeated samples can look like optimization

Suppose one draw has probability u of being an optimal feasible subset. Independent draws miss every optimum with probability (1-u)^S. Therefore:

$$
P(\text{at least one optimum})=1-(1-u)^S.
$$

For uniform feasible sampling with one optimum among M subsets, u=1/M. With n=10 and k=5, M=10!/(5!5!)=252. At S=1,024, optimum coverage is approximately 0.9829. This is already high without a learned distribution. With n=16,k=5, M=4,368 and coverage is approximately 0.2090. A small exact-solver comparison can hide this distinction if it reports only the best of many samples.

Uniform feasible sampling is easy here: choose exactly k distinct indices uniformly, evaluate their objective, and keep the best. This baseline has no variational-angle training. QAOA's final 1,024 draws are additional to up to 64 objective evaluations used to choose angles. An equal-final-draw comparison is useful but is not equal-total-compute or a hardware speed comparison.

### Feasibility and expected best energy

Let F be the total single-draw probability on feasible subsets. Then the probability of obtaining no feasible subset in S draws is (1-F)^S. Ideal count-preserving execution gives F=1 up to numerical roundoff. A squared penalty gives no such finite-depth guarantee. We keep zero-feasible outcomes as failures; reporting only the successful subset of circuits would censor this cost.

To compute the expected best feasible energy, sort feasible states by energy e_1 <= ... <= e_M and let their raw probabilities be p_1,...,p_M. They sum to F and need not sum to one. Write C_j=sum from t=1 to j of p_t, with C_0=0. The probability that the best feasible sample has energy e_j is:

$$
w_j=(1-C_{j-1})^S-(1-C_j)^S.
$$

To see why, the first term says no sample has an energy smaller than e_j; the second removes the case where none has energy at most e_j either. Ties may be listed in any stable order because their energy is identical. These weights sum to 1-(1-F)^S, the chance of at least one feasible draw. Thus the conditional expected best energy is sum_j(e_j*w_j) divided by 1-(1-F)^S. Subtracting the exact feasible optimum gives the conditional expected energy gap. The conditioning must be shown beside no-feasible probability so it does not hide failure risk.

The [sampling study](../scripts/sampling_coverage_study.py) evaluates these expressions using trained ideal statevectors on 20 real development-derived instances, four nested candidate sizes, two encodings and three seeds: 480 circuit solves. It uses no generated answers and no support labels. Floating-point probability sums are clipped to [0,1] at their numerical boundary, preventing an impossible negative failure probability of order 10^-15. The first numerical export is retained locally as an archive; this is a roundoff correction, not an outcome-based algorithm change.

## Reading statistical comparisons correctly

For question q, let d_q be method A's F1 minus method B's F1 after averaging each method's seeds. The estimated difference is the arithmetic mean of d_q across the N common questions. A paired bootstrap samples N question IDs with replacement, recomputes that mean, and repeats 10,000 times. The 2.5th and 97.5th percentiles give the reported 95% interval. Pairing preserves the fact that both methods face the same easy or difficult question.

If three seeds on one question score 1, 0.5 and 0, that question contributes 0.5. It does not become three independently sampled questions. If the last seed fails, its F1 remains zero and the mean is still 0.5. In contrast, missing resource measurements remain missing: inventing a gate count of zero for an unexecuted circuit would also bias a resource mean. Completed circuits with measured zero feasibility do contribute their actual zero.

An interval entirely above zero supports a positive difference under this sample and analysis. An interval spanning zero leaves both positive and negative effects plausible. It does not establish that the methods are equal. Noninferiority would require a chosen acceptable loss and a suitable interval bound declared before looking at the result. This project does not retrospectively invent such a tolerance.

The question is the resampling unit, but source passages and compositional question templates can still be shared across questions. The bootstrap does not model every such cluster. The two generators are from one family, and numerical simulator training is not physical-device execution. These limits restrict generalization even when a difference looks clear. Secondary exploratory tables are not a large collection of independent confirmatory discoveries.

## Artifact checks and independent reconstruction

A result is traceable when a table cell can be followed to question scores, predictions, selected IDs, objective coefficients and the exact code/configuration that produced them. Checksums detect changed bytes; they do not establish scientific correctness. The [final auditor](../scripts/audit_final_runs.py) additionally recomputes answer scores, source membership, count/token constraints and pair-sum energies, and retokenizes saved prompts against pinned tokenizers. A failed invariant stops assembly rather than silently correcting a scientific record.

Compact public predictions omit large prompts and parameter traces but preserve the fields needed to regenerate tables, with a SHA-256 digest of their compressed file. [Public-table reconstruction](../scripts/reproduce_public_tables.py) needs neither model weights nor raw dataset text. This tests statistical reconstruction from released outcomes; it is different from rerunning retrieval, selection and generation. Full local artifacts and split/corpus restoration scripts support that more expensive route.

For numbers that are mathematically equivalent but differ slightly in floating-point reduction order on another machine, reconstruction accepts an absolute/relative tolerance of 10^-12. It still requires identical structure, IDs, counts and file hashes. Tolerance is not permission to substitute different predictions.

### A container image and a dependency lock solve different problems

A lock records exact package versions. An image packages an installed operating-system/runtime filesystem. Pinning the base-image digest fixes its bytes, while pinning runtime dependencies prevents a rebuild from silently adopting newer libraries. Neither fixes the host kernel, CPU/GPU hardware or every external driver. The CPU service and CUDA experiments deliberately have different environment snapshots; passing a CPU service check is not evidence of bit-identical GPU outputs.

The container runs as a nonroot user, mounts weights read-only and stores mutable indexes/jobs in a separate named volume. This separates immutable inputs from runtime state. Removing a disposable container need not remove that named volume. Restart recovery can then distinguish completed jobs from interrupted ones. These mechanisms are useful in other model services even when no quantum component exists.

Correctness tests also have dependency boundaries. The lightweight workflow checks the available baseline contracts and explicitly skips integrations whose optional packages are absent. The fuller research workflow installs Qiskit/FAISS/service dependencies and executes those integrations. A skip is visible absence of a check, not a passed execution; the full suite currently has 46 tests. Testing source spectra, feasibility and probability sensitivity with actual Qiskit is different from exercising HTTP state transitions with an explicitly labeled fake inference engine.
