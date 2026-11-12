// Editorial content. Numbers and full reference text are assembled from tracked artifacts.
const ref = (doc, section, label) => ({ doc, section, label });
const foundations = (section, label = "Derivation and implementation detail") =>
  ref("foundations", section, label);
const report = (section, label = "Measured results and boundaries") =>
  ref("report", section, label);
const chapters = [
  {
    id: "overview",
    title: "The whole project",
    eyebrow: "01 / ORIENTATION",
    subtitle: "From a question to a defensible answer.",
    lead: "Follow how passages become context, how context becomes an answer, and how the experiment tells us whether a selection method helped.",
    body: `### The question behind Q-RAG
A language model can answer fluently while missing the facts it needs. Retrieval augmented generation (RAG) supplies external text. This project studies **which subset of candidate passages should reach the generator**, particularly when an answer requires several passages together.

Consider the fictional question **“In which country was the director of Film A born?”** One source identifies Maya Rao as the director. A second says Maya Rao was born in India. A release-date passage is related to Film A but cannot complete that chain.

The research separates three responsibilities:
1. **Representation and scoring:** estimate which passages and pairs are useful.
2. **Selection:** choose a subset under a declared budget.
3. **Generation and evaluation:** ask a fixed language model to answer, then compare its output with reference annotations.

A failure can occur in any of these stages. Optimizing a score perfectly does not make the score a perfect model of useful evidence.

### What was actually built
The implementation includes token-safe embeddings, caches and search indexes; lexical, dense and reranking references; constrained MILP and heuristic selection; entity-link features; four sparsification policies; simulated QAOA; real local answer generation; dataset-specific evaluation; reproducible artifacts; and a separate API and interactive laboratory.

### Read the findings with their scope
The saved study contains **1,000 distinct held-out questions** across HotpotQA and MuSiQue. Repeating methods, seeds and generators yields **53,230 method/question records across 24 runs**, including 21 failures. Those repetitions are not additional independent questions.

The proposed evidence-guidance benefit was **not established**. All quantum execution was simulated. The valuable research question is what encoding, initialization, sampling and scoring do to this particular context-selection pipeline; practical quantum advantage is not demonstrated.`,
    widget: "pipeline",
    deep: [
      ref("readme", "", "Full project overview"),
      foundations("the-system-and-the-problem-it-solves"),
      ref("claims", "", "Claims and their exact evidence"),
    ],
    questions: [
      [
        "If a selector retains the annotated evidence but the answer is wrong, must the selector be faulty?",
        "No. Generation, formatting, ambiguous references or other factors may be responsible. Evidence retention and answer correctness are different measurements.",
      ],
    ],
  },
  {
    id: "state",
    title: "Where it stands",
    eyebrow: "02 / CURRENT STATE",
    subtitle: "Implementation complete within a bounded scope.",
    lead: "Distinguish the delivered software, the tested hypothesis and the remaining scientific work.",
    body: `### Three meanings of completion
**Software completion:** the documented components and scoped local runs exist. **Research outcome:** the experiments answer a bounded question, including unfavorable results. **Publication readiness:** humans have verified the contribution, methods, claims and submission package. These are separate milestones.

### What the completed run supports
- Real answer generation and official-style scoring on two datasets.
- Classical comparisons with 500 held-out questions per dataset and generator.
- Main quantum comparisons on 50 questions per dataset, relevance-reduced pools of at most ten candidates and three seeds averaged within question.
- Separate prepared-circuit, formulation, gate-cap, token-budget and bounded-corpus controls.
- Recorded failures, circuit resources, hashes and reproducible numerical tables.

### What remains outside the claim
There is no physical quantum execution, proven quantum advantage, independently verified factual knowledge graph, demonstrated evidence preservation, independent scientific review or publication acceptance. Typed factual relation extraction and quantum token-budget circuits were not implemented.

The local service is a demonstration, not a production deployment. A reviewed manuscript layout is not scientific peer review. Automated artifact checks are not independent human replication.

### Historical statements stay historical
The three-question November 4 baseline and earlier “next” milestones explain how the system developed. They do not override the final state. Read later corrections together with original results: the basis-start circuit and the prepared extension remain separate experiments.`,
    deep: [
      report(
        "coverage-of-the-original-plan-and-explicit-gaps",
        "Original-plan coverage and explicit gaps",
      ),
      ref(
        "sequence",
        "current-state-after-the-full-local-run",
        "Current phase-status table",
      ),
      ref("handoff", "", "Outstanding external work"),
    ],
    questions: [
      [
        "Does passing all correctness tests establish that the method improves answer quality?",
        "No. Tests check specified contracts and numerical properties. Comparative held-out answer measurements are needed to establish task performance.",
      ],
    ],
  },
  {
    id: "plan",
    title: "The original plan",
    eyebrow: "03 / RESEARCH INTENT",
    subtitle: "A hypothesis, then an experiment.",
    lead: "The plan explains why the phases exist. The current report explains what they delivered.",
    body: `### The original research question
Could question-specific evidence links guide removal of pairwise interactions, preserving useful answer context while reducing QAOA circuit resources?

The planned chain was **reproducible environment → trustworthy data → retrieval → constrained classical selection → quantum circuits → sparsification → controlled evaluation → manuscript and demonstration → release**.

### Why establish classical methods first?
MILP and tiny exhaustive checks provide a reference for the same coefficient arrays and feasible set. If a graph feature fails under classical selection, changing the solver does not automatically repair the feature. Scoring improvements and solver improvements must be evaluated separately.

### Why the scope changed
Development measurements did not justify promising preserved answer quality. The work continued as an **encoding-aware empirical comparison**. A cardinality penalty can make a sparse objective dense again; feasible mixing has its own preparation and routing costs; best-of-many sampling is a strong control in tiny spaces.

This is a documented change in research interpretation, not permission to discard unfavorable results. A negative finding is useful only when its experimental design and generalizable insight are defensible.

### Read the plan as a plan
The original execution document includes proposed interfaces, conditional components and a historical schedule. The completed implementation uses JSON/JSONL artifacts rather than a separate tracking server, a static dashboard rather than a large frontend framework, and laptop simulation rather than quantum hardware. The coverage assessment records the remaining differences.`,
    deep: [
      ref("plan", "", "Complete original implementation plan"),
      ref("sequence", "", "Full development sequence"),
      report("coverage-of-the-original-plan-and-explicit-gaps"),
    ],
    questions: [
      [
        "Why is implementing every planned feature insufficient for a research contribution?",
        "A contribution needs an original, significant and well-supported finding. A feature inventory alone does not establish novelty or usefulness.",
      ],
    ],
  },
  {
    id: "foundations",
    title: "Build the foundations",
    eyebrow: "04 / CONCEPTS & MATHEMATICS",
    subtitle: "Understand the objects before the algorithms.",
    lead: "Start with text, vectors and labels. Then build the objective and evaluate an answer.",
    body: `### Inference inputs and reference annotations
The selector receives the question, source text and provenance. The evaluator separately receives expected answers, aliases and annotated support. Giving the selector the answer key would invalidate the comparison. An oracle diagnostic deliberately uses gold support and is explicitly labelled; ordinary inference does not.

### Tokens, chunks and embeddings
Tokens are model-specific text units, not words. MiniLM has a limited input length. The main study creates traceable chunks of at most **240 embedding tokens**, including special tokens and a bounded title prefix. Long sentences use overlapping windows. All chunk vectors contribute to a normalized document representation; small important facts can still be diluted by averaging.

For unit chunk vectors $z_j$, document vector $v$ and unit question vector $u$:

$$
\\bar v=\\frac1m\\sum_{j=1}^m z_j,\\qquad v=\\frac{\\bar v}{\\|\\bar v\\|_2},\\qquad r_i=u^\\top v_i.
$$

With document rows $D$, relevance is $r=Du$ and pair similarity is $DD^\\top$. The vectors have 384 coordinates. Similarity is not the probability of a true answer. A cache avoids repeating an embedding calculation; an index finds stored vectors relevant to a query. These are different tools.

### A subset is a binary decision
$x_i=1$ means passage $i$ is selected. The full objective is:

$$
E(x)=-\\alpha\\sum_i r_i x_i+\\sum_{i<j}\\left(\\beta\\max(s_{ij},0)-\\gamma C_{ij}\\right)x_i x_j.
$$

Relevance is rewarded, positive similarity is a redundancy penalty, and the entity-link proxy $C_{ij}$ rewards possible complementarity. The final study fixes $\\alpha=1$, $\\beta=0.2$ and development-selected $\\gamma=0.2$. Only the strict upper triangle is stored, so each pair contributes once.

A fixed-count constraint is $\\sum_i x_i=k$. The separate classical token study uses $\\sum_i t_i x_i\\le B$ and a nonempty selection. Equal count does not imply equal tokens.

### Generation is another model operation
The project uses frozen pretrained MiniLM and Qwen weights; it does not fine-tune them. The same prompt, ordering policy and decoding settings are shared within comparisons. Circuit-angle optimization does not update the LLM.

### Evaluation has two different targets
Answer exact match and token F1 evaluate generated text. Document precision, recall and complete support evaluate selected annotations. They cannot be substituted for one another. If multiset token overlap is $m$, predicted token count is $P$ and reference count is $G$:

$$
\\mathrm{precision}=m/P,\\quad\\mathrm{recall}=m/G,\\quad F_1=\\frac{2m}{P+G}.
$$

For “red red blue” versus “red blue blue”, overlap is two and F1 is $2/3$. Dataset-specific normalization, aliases and empty/special-answer rules matter. Mean per-question F1 differs from F1 calculated after pooling tokens. Failed method executions remain zero in answer averages.`,
    widget: "objective",
    deep: [
      foundations("data-contracts-and-label-isolation"),
      foundations("tokens-embeddings-and-transformer-representations"),
      foundations("similarity-derivation-and-array-shapes"),
      foundations("the-selection-objective-and-its-interpretation"),
      foundations("from-binary-quadratic-optimization-to-milp"),
      foundations("answer-generation-and-inference-behavior"),
      foundations("evaluation-with-worked-calculations"),
      foundations("a-complete-trace-through-the-actual-first-question"),
      foundations("graph-and-quantum-foundations"),
    ],
    questions: [
      [
        "Can a relevance value of 0.8 be interpreted as an 80% chance of containing the answer?",
        "No. It is a cosine similarity between learned representations, not a calibrated support probability.",
      ],
      [
        "Why can an exact MILP optimum give a worse answer than relevance ranking?",
        "MILP optimizes a proxy objective. That objective contains no guarantee about the generator or reference-answer correctness.",
      ],
    ],
  },
  {
    id: "research",
    title: "Make a fair experiment",
    eyebrow: "05 / PRIOR WORK & PROTOCOL",
    subtitle: "Separate a new score from a better solver.",
    lead: "A convincing result depends on the comparison contract, not just the winning number.",
    body: `### The contribution boundary
Passage-set selection, QUBO evidence selection, graph retrieval, QAOA and graph sparsification all have prior work. The project does not invent these foundations or provide a new sparsification theorem. Its candidate contribution is a controlled evaluation of how they interact under context constraints and complete circuit accounting.

The literature matrix is bounded and dated. An exact original-model reproduction of SetR or the closest QUBO selector is not complete; the lexical coverage reference is an explicitly different adaptation. The manuscript needs a refreshed closest-work search and substantive external review before submission.

### Three research questions
1. Does the query-conditioned entity-link feature improve generated answers under the same budget?
2. Does protecting possible evidence links outperform generic sparsification under matched interaction budgets?
3. How do penalty and count-preserving encodings change feasibility, quality and complete compiled cost?

### The comparison contract
Within each condition, share candidate passages, input order, model revisions, prompt policy, decoding and constraints. Evaluate scoring changes with common solvers, and solver changes with common coefficients. Report count and token conditions separately. Candidate reduction must not consult answer annotations.

Freeze development decisions and held-out IDs before inspecting final results. Retain all seeds and failures. Adding a control after a diagnosis is allowed, but it must be labelled exploratory and must not replace the original result silently.

### Uncertainty belongs to questions
Average solver seeds within each question, then bootstrap paired question differences. The final analysis uses 10,000 resamples and 95% percentile intervals. An interval crossing zero does not prove equality. Preserved quality requires an appropriate predeclared noninferiority design; one was not frozen here.

The source documents below include historical venue information. Their dates are snapshots, not a live deadline feed.`,
    deep: [
      ref("literature", "", "Full related-work matrix and search limits"),
      ref("protocol", "", "Complete frozen experimental protocol"),
      foundations("reading-statistical-comparisons-correctly"),
      ref("claims", "", "Measured claims versus unverified work"),
    ],
    questions: [
      [
        "Why are three solver seeds on 50 questions not 150 independent questions?",
        "The seeds repeat computation on the same questions. They share the question and evidence; average within question before question-level uncertainty estimation.",
      ],
    ],
  },
  {
    id: "implementation",
    title: "Build it phase by phase",
    eyebrow: "06 / DEVELOPMENT EXPLORER",
    subtitle: "Why → mathematics → implementation → evidence.",
    lead: "Move through the historical baseline and phases A–I. Each phase connects a need to a concrete component, its checks and its limits.",
    body: "",
    deep: [],
    questions: [],
  },
  {
    id: "results",
    title: "Read the actual results",
    eyebrow: "07 / MEASURED EVIDENCE",
    subtitle: "What changed—and what was not established.",
    lead: "Explore the saved comparisons. These charts read tracked analysis artifacts; they do not launch new experiments.",
    body: `### Begin with the denominator
The primary matrix contains 18 conditions and 50,290 method/question evaluations over 1,000 distinct held-out questions. Six scoped controls bring the total to 24 runs and 53,230 records: 53,209 successful and 21 failed. Main classical count comparisons use 500 questions per dataset/generator. Main quantum comparisons use 50 per dataset, at most ten candidates and three averaged seeds.

### Four findings to carry forward
**Lexical coverage has the highest observed F1** in all four main classical count settings. That is an observed ranking, not a universal superiority theorem.

**Evidence-guided half-edge sparsification does not establish a benefit.** Evidence-minus-magnitude differences are −0.0363 F1 on HotpotQA and −0.0095 on MuSiQue; both paired intervals cross zero. Prepared controls also fail to establish a consistent benefit.

**Constraint encoding changes resources.** A squared count penalty introduces all-pairs couplings. XY count preservation avoids that particular penalty but adds mixer/preparation costs. Generic synthetic-line compilation is not a minimum-gate proof or a physical timing measurement. The known-basis first cost layer can be redundant; state-aware simplification remains a review concern.

**Lower energy can accompany worse answers.** Full MILP has lower common-objective energy but worse F1 than relevance ranking on 31, 37, 36 and 32 questions across the four main count conditions. This is an observed proxy mismatch, not independent causal annotation of graph or generator errors.

### Comparisons that must stay separate
The 1,200-token conditions use 100 questions, while count conditions use 500. The 25-candidate corpus studies use 100 questions; 50/100-candidate studies use 30. Their raw means do not isolate a causal effect across different populations. Larger one-second MILPs are not all certified optimal. Larger quantum sensitivities are only five MuSiQue questions per size.

### Failures and output limits
One main penalty run produced no feasible sample. Twenty gate-cap diagnostic records could not satisfy the imposed cap; these remain failures. The audit flags 914 successful records reaching the 32-new-token generation allowance, which indicates possible truncation rather than proving every answer is incomplete. These are records, not distinct neural calls.`,
    widget: "results",
    deep: [
      report(
        "phase-g--definitive-evaluation-and-independent-audit",
        "Full definitive evaluation",
      ),
      report("generation-length-limits-in-the-completed-evaluation"),
      ref("main-results", "", "All headline tables"),
      ref("sampling-results", "", "Distribution and sampling study"),
      ref("error-analysis", "", "Error signatures and real examples"),
      ref("claims", "", "Claim-to-artifact map"),
    ],
    questions: [
      [
        "A sparse method uses fewer gates and its F1 interval crosses zero. Can we claim preserved answer quality?",
        "No. A nonsignificant difference does not establish noninferiority. Also check that the circuit resource comparison includes all operations and uses an appropriate implementation.",
      ],
    ],
  },
  {
    id: "reproduce",
    title: "Follow the evidence",
    eyebrow: "08 / REPRODUCIBILITY",
    subtitle: "A number should have a traceable path.",
    lead: "Connect configuration, exact inputs, recorded outcomes, statistical reconstruction and the scientific claim.",
    body: `### Three levels of reproduction
1. **Rebuild saved tables:** read public compact predictions and recompute statistics. No model weights or raw passages are needed.
2. **Rerun fixed solver instances:** load frozen coefficients/constraints, execute MILP or simulated QAOA, and compare selections, energies and compiled costs. The bundle contains 110 instances.
3. **Rerun end-to-end inference:** restore datasets, model revisions and configurations; rebuild representations and generate answers. This is a different and more expensive check.

### The recorded chain
A configuration declares intended settings. A manifest adds input hashes, software, model revisions, IDs and backend information. An append-only journal records attempts and protects successful outcomes during resume. Summaries and paired intervals derive from those records; the manuscript assembler fills named numerical blocks.

SHA-256 identifies bytes; it does not establish that the bytes are scientifically correct. Seeds improve repeatability; they do not prevent leakage or guarantee identical kernels across machines. A source snapshot archives the calculation, whereas a hash alone does not.

### Try the model-free checks
These commands are optional hands-on verification; understanding the results does not require leaving this website.

~~~bash
venv/bin/python scripts/reproduce_public_tables.py --verify
venv/bin/python scripts/reproduce_quantum_instance.py --verify-recorded
~~~

The full in-site references include installation choices, exact input restoration and inference commands. The CPU container, CI and CUDA laptop have separate recorded environments. Automated reconstruction and a human independently reviewing the science are different checks.`,
    widget: "artifacts",
    deep: [
      ref("reproducibility", "", "Complete reproduction guide"),
      ref("claims", "", "All claims and supporting artifacts"),
      foundations("reproducibility-and-software-contracts"),
      foundations("artifact-checks-and-independent-reconstruction"),
    ],
    questions: [
      [
        "If a published table reconstructs exactly, what remains unverified?",
        "It establishes consistency with saved outcomes, not that retrieval and generation were rerun, the design is unbiased, or the interpretation is correct.",
      ],
    ],
  },
  {
    id: "system",
    title: "Use the working system",
    eyebrow: "09 / ENGINEERING & LIVE LAB",
    subtitle: "The experiment becomes an inspectable service.",
    lead: "The live laboratory uses the research library. The guided journey itself requires neither model loading nor dataset downloads.",
    body: `### What happens when Compare methods is pressed?
The browser submits a question, source texts, count and method names to a FastAPI service. Strict request validation checks boundaries. A bounded queue returns a job ID. One inference worker loads pinned local MiniLM/Qwen models lazily, computes features, selects contexts and generates answers. The browser polls the job and renders its actual state.

The current laboratory offers relevance, MMR, MILP and simulated QAOA. All use a common pool; QAOA requests above ten sources reduce every compared method to the same relevance-based ten. Equal ordered contexts reuse deterministic generation. Results identify supplied text, tokens, objective, status, timing and explicit fallback. They do not prove the LLM used every source or automatically score live answer correctness.

### What the interface does not expose
The live QAOA option is the frozen basis-start XY depth-one implementation. The prepared control and research sparsification matrix remain separate experiments. The API supports bounded corpus ingestion/query, but the current laboratory page edits supplied passages. No physical QPU is connected.

### Engineering concepts that transfer
SQLite caches avoid repeated computation; persistent indexes bind vectors to provenance. Durable job state supports restart recovery. Readiness differs from process health: a service can respond before weights are loaded. OpenTelemetry separates preparation, embedding, graph, selection and generation spans. A nonroot CPU container mounts weights read-only and keeps mutable state in a named volume.

GPU batching increases work per embedding call, amortizing overhead while consuming memory. It was profiled on 128 chunks; it does not imply continuously batched generation. Five fictional repeated API comparisons give scoped latency measurements, not a production service guarantee.

### Open the laboratory when ready
Use the **Live laboratory** link to try an example. This is optional: the educational examples and saved results here are fully readable while models are cold. The service is intended for loopback use and is not a hardened public deployment.`,
    deep: [
      ref("service", "", "Full service and dashboard guide"),
      foundations("service-foundations--requests-jobs-and-observability"),
      foundations("dashboard-foundations--state-rendering-and-local-assets"),
      foundations(
        "interactive-walkthrough-mathematics-and-content-provenance",
        "All walkthrough examples and the content-build contract",
      ),
      report("phase-h--actual-service-persistence-and-batching-measurements"),
    ],
    questions: [
      [
        "Why can health succeed while readiness fails?",
        "Health checks that the process can answer requests. Readiness additionally requires the models and required inference resources to be available.",
      ],
    ],
  },
  {
    id: "paper",
    title: "The paper & next questions",
    eyebrow: "10 / SYNTHESIS & FUTURE WORK",
    subtitle: "Turn measurements into a defensible argument.",
    lead: "Read the complete manuscript here, then distinguish future experiments from existing evidence.",
    body: `### The argument of the manuscript
The paper evaluates context selection through a common objective and controlled generation. It explains signed sparse surrogates, penalty versus feasible-subspace encoding, complete circuit costs, the basis-start global phase and same-draw sampling controls. It reports both datasets and unfavorable comparisons.

The scientific conclusion is bounded: **constraint encoding and state preparation must be part of resource accounting; this setup does not establish an evidence-guidance benefit or practical quantum advantage**. Neither the elementary coefficient bound nor a polished service is a novelty certificate.

### What would strengthen the next study?
- Validate entity identities and useful evidence bridges on a documented independent annotation sample; the existing 40-edge worksheet is unjudged.
- Strengthen preparation and optimization controls, retain the original diagnosis, and check known-state circuit simplifications before making resource claims.
- Refresh closest-work comparisons and reproduce accessible external methods with clear estimator/model differences.
- Design new frozen experiments around a focused question, with suitable sample sizes and budgets. More trials should answer a question, not continue until a favorable result appears.
- Add a small physical-device pilot if account access is available. Simulation-trained/hardware-evaluated circuits and hardware-in-the-loop optimization are different experiments. A QPU run alone would not establish an advantage over classical methods.

### Publication and responsibility
The current artifact is a research preview, not an accepted paper. Actual authors must understand, verify and approve the final work, agree contributions and rights, retain an accurate substantive AI-assistance disclosure, choose a suitable venue and satisfy its current rules. A preprint is not peer-reviewed acceptance. Venue dates in the archived guide require fresh verification.

### What is deliberately not claimed
No hardware speedup, verified factual knowledge graph, universal failure of quantum RAG, proven evidence preservation, production deployment or exhaustive novelty. These boundaries keep the next research question specific and testable.

Open the complete manuscript and final handoff below. The full research argument, mathematical background, phase history and result tables are available in this website; original files remain optional provenance.`,
    deep: [
      ref("manuscript", "", "Complete manuscript with figures and results"),
      ref("handoff", "", "Remaining external work"),
      ref("rights", "", "Rights and upstream attribution"),
      ref("publication", "", "Dated publication preparation guide"),
      foundations("versioned-release-versus-scientific-acceptance"),
    ],
    questions: [
      [
        "Would executing the same small circuits on hardware demonstrate quantum advantage?",
        "No. It would establish physical execution. Advantage needs a meaningful, fairly budgeted comparison against strong classical alternatives, with appropriate performance evidence.",
      ],
    ],
  },
];
const phases = [
  {
    id: "baseline",
    title: "The historical baseline",
    tag: "NOVEMBER 4 / HISTORICAL",
    why: "The prototype measured selected documents but did not establish that generated answers improved. Unequal selected counts also made recall comparisons unfair.",
    how: "Separated inference inputs from labels, implemented common metrics and a signed objective, added native fixed-count MILP and an exhaustive oracle, then used the same local generator and ordering policy for both methods.",
    math: "Binary products become continuous auxiliary variables with exact bounds. This is discrete optimization, not setting a derivative to zero.",
    result:
      "On three development questions, both methods had answer EM/F1 of 1/3. MILP selected more annotated support and lower objective values, but contexts were longer in tokens and aggregate answer quality did not improve.",
    boundary:
      "Three inspected questions are an execution check, not a significant comparative result. The film/person reference anomaly was also present upstream; one anomaly does not estimate label error across the dataset.",
    widget: "milp",
    deep: [
      ref(
        "sequence",
        "historical-baseline-sequence--november-49",
        "Baseline implementation order",
      ),
      foundations("from-binary-quadratic-optimization-to-milp"),
      foundations("a-complete-trace-through-the-actual-first-question"),
      report("verified-development-experiment"),
      ref("baseline", "", "Historical runner commands"),
    ],
  },
  {
    id: "a",
    title: "A · Reproducible foundations",
    tag: "ENVIRONMENT / PROTOCOL",
    why: "A package list is not proof that the laptop can execute a tensor operation, quantum simulation or optimizer correctly.",
    how: "Measured the host, performed real CUDA/Bell-state/MILP checks, recorded dependency/model identities, reviewed related work and froze the experimental contract. CI checks numerical and software contracts.",
    math: "The tiny binary check minimizes −x for x∈{0,1}, whose optimum is x=1. A Bell-state smoke has ideal probabilities (1/2,0,0,1/2). Seeds, hashes and locks answer different reproducibility questions.",
    result:
      "The scoped environment probes and configurations support the subsequent local runs. They do not certify novelty, absence of bias or portability across every future machine.",
    boundary:
      "The literature search is bounded. The CUDA laptop, lighter CI and CPU-container environments are separate snapshots.",
    deep: [
      foundations("phase-a-foundations--what-reproducibility-establishes"),
      report(
        "phase-a--measured-environment-and-research-protocol-november-10-2026",
      ),
      ref("protocol", "", "Frozen questions and controls"),
      ref("reproducibility", "", "Environment details"),
    ],
  },
  {
    id: "b",
    title: "B · Data and trustworthy scoring",
    tag: "ANNOTATIONS / HELD-OUT SPLITS",
    why: "A selector must never see reference answers or supporting-fact labels. Dataset-specific scoring conventions must remain correct.",
    how: "Built HotpotQA and MuSiQue adapters, stable source/sentence identities, fresh frozen splits, duplicate audits and checks against official metric semantics. Ran empty-context and gold-evidence diagnostics as explicitly separate controls.",
    math: "Token F1 uses multiset overlap. Jaccard overlap of token-trigram sets flags near-duplicate questions. Supporting paragraph IDs are not interchangeable with display titles.",
    result:
      "Each dataset has 100 development and 500 held-out questions. Final IDs come from official validation/dev material, not a hidden benchmark test set.",
    boundary:
      "Question deduplication cannot eliminate every paraphrase, shared source or pretrained-model exposure. Oracle labels are for diagnosis only.",
    deep: [
      foundations(
        "phase-b-foundations--annotations-aliases-and-dataset-specific-scoring",
      ),
      report("phase-b--data-boundaries-frozen-splits-and-scorer-verification"),
      foundations("evaluation-with-worked-calculations"),
    ],
  },
  {
    id: "c",
    title: "C · Chunks, caches and retrieval",
    tag: "REPRESENTATION / SEARCH",
    why: "Whole-passage embeddings silently omitted long-text tails. Repeating embeddings wasted work; corpus search needed persistent vector/provenance consistency.",
    how: "Added 240-token sentence-aware chunks, overlapping oversized-sentence windows, exact offsets, normalized chunk aggregation, content-addressed embedding caches and checked FAISS/SQLite bundles. Added BM25, rank fusion and chunk-aware reranking.",
    math: "Normalize the mean of unit chunk vectors, compare with a unit query by dot product, and search exact inner products. Reciprocal-rank fusion adds 1/(60+rank), avoiding incompatible raw score scales.",
    result:
      "Later text contributes to document representations, caches persist across runs and index restoration is checked. Actual token lengths and GPU batch profiles were recorded.",
    boundary:
      "Averaging can dilute a local fact. Exact search is linear in stored-vector count, not free or approximate-nearest-neighbour scaling. Retrieval measurements are workload-specific.",
    deep: [
      foundations("phase-c-foundations--chunking-caches-ranking-and-indexes"),
      report("phase-c--token-safe-retrieval-cache-and-persistent-index"),
      foundations("phase-g-preparation--bounded-corpora-and-measuring-memory"),
    ],
  },
  {
    id: "d",
    title: "D · Constrained selection and evidence",
    tag: "FORMULATION / CLASSICAL CONTROLS",
    why: "Without common budgets and a strong classical reference, an apparent quantum gain could come from a different objective or extra context.",
    how: "Added signed MILP, native count/token constraints, greedy/MMR/coverage/annealing references and source-grounded entity-link extraction with caching. Feature construction uses only allowed question/text inputs.",
    math: "The complementarity proxy is Cᵢⱼ=Lᵢⱼ max(aᵢ,aⱼ)√(max(rᵢ,0)max(rⱼ,0)). Pair coefficients are β max(sᵢⱼ,0)−γCᵢⱼ. Native classical constraints avoid a quantum penalty encoding.",
    result:
      "MILP matches exhaustive enumeration on tested tiny signed problems. Solver statuses distinguish certified optima from time-limited incumbents. The graph contributes a transparent scoring feature, not verified semantic facts.",
    boundary:
      "The 40-edge independent annotation worksheet is unjudged. Lexical coverage is not an exact SetR reproduction. An optimal proxy objective need not give the most accurate answer.",
    widget: "objective",
    deep: [
      foundations(
        "phase-d-foundations--budgets-heuristics-and-graph-coefficients",
      ),
      report(
        "phase-d--constrained-selectors-and-transparent-evidence-features",
      ),
      foundations("from-binary-quadratic-optimization-to-milp"),
    ],
  },
  {
    id: "e",
    title: "E · The quantum calculation",
    tag: "SIMULATED QAOA / CIRCUIT ACCOUNTING",
    why: "A quantum wrapper alone does not establish a meaningful experiment. The mapping, feasibility, optimizer budget and entire circuit need checks.",
    how: "Constructed Qiskit cost/mixer circuits, verified all basis-state energies on small signed examples, trained angles with COBYLA, sampled final bitstrings and compiled complete circuits. Compared penalty and count-preserving XY encodings.",
    math: "Use xᵢ=(1−Zᵢ)/2 to map binary coefficients to Ising fields/couplings. The count penalty λ(Σxᵢ−k)² adds all-pairs terms. Paired RXX/RYY gates exchange 01 and 10 and preserve the number selected ideally.",
    result:
      "Actual simulated circuits execute. Ideal XY measurements preserve count; penalty measurements can be infeasible. Artificial-noise final-sampling diagnostics are separate from ideal angle training.",
    boundary:
      "The original basis-start first cost phase is global and inactive in probabilities. A separately hashed prepared-superposition control addresses that degeneracy, but is exploratory. No QPU, physical-noise training or quantum token-budget circuit is claimed.",
    widget: "quantum",
    deep: [
      foundations("qubo-and-ising-mapping"),
      foundations(
        "phase-e-foundations--deriving-the-implemented-quantum-calculation",
      ),
      foundations("sampling-state-preparation-and-a-weak-depth-one-circuit"),
      foundations("why-the-paired-xy-gates-preserve-passage-count"),
      report("phase-e--actual-qaoa-feasibility-and-circuit-resources"),
    ],
  },
  {
    id: "f",
    title: "F · Sparsify and test the hypothesis",
    tag: "EDGE BUDGETS / DEVELOPMENT DECISION",
    why: "Removing interactions might reduce circuit resources, but retaining semantic edges is useful only if it beats appropriate controls.",
    how: "Implemented magnitude, seeded random, endpoint-degree and evidence-guided retention at exact unordered-edge budgets. Selected gamma on development data only and recorded both surrogate and original energies.",
    math: "For removed coefficient mass δ=Σ|bᵢⱼ|, every binary vector satisfies |E−Ẽ|≤δ. An ε-suboptimal sparse solution over the same feasible set has full-objective gap at most 2δ+ε. This is not an answer-F1 guarantee.",
    result:
      "Gamma 0.2 maximized the equal-weight development average among the tested values. Development findings did not justify claiming evidence preservation, so the study continued as a controlled comparison.",
    boundary:
      "Count penalties can erase symbolic sparsity. Removed edge count is not compiled gate count. A sampled QAOA result does not have a known ε certificate without a separate bound or optimum.",
    widget: "sparsify",
    deep: [
      foundations("sparsification-changes-the-optimization-problem"),
      foundations(
        "phase-f-foundations--exact-edge-budgets-and-what-sparsification-can-prove",
      ),
      report(
        "phase-f--calibrated-weights-sparsification-and-research-decision",
      ),
    ],
  },
  {
    id: "g",
    title: "G · Freeze, execute and interpret",
    tag: "DEFINITIVE EVALUATION",
    why: "Development wins can disappear on fresh data. Best-of-many samples can appear strong simply because the feasible space is tiny.",
    how: "Froze the main matrix and question IDs, retained a Unicode-provenance restart with unchanged scientific settings, executed all declared conditions, audited records and reconstructed paired statistics. Added separately scoped mechanism/preparation controls.",
    math: "At n=10,k=5, there are 252 feasible subsets. The probability of seeing one fixed optimum in S independent uniform feasible draws is 1−(1−1/252)^S. Seeds are averaged within question before bootstrap resampling.",
    result:
      "24 complete runs contain 53,230 records. The proposed guidance benefit and quantum advantage are not established. Lexical coverage leads the observed main classical count means. The original and prepared quantum results remain separately labelled.",
    boundary:
      "Only 50 questions per dataset underpin the main quantum comparisons. Shared generator family, bounded corpora, output limits and time-limited larger MILPs restrict generalization. An interval crossing zero does not establish equality.",
    widget: "sampling",
    deep: [
      foundations("how-repeated-samples-can-look-like-optimization"),
      foundations("reading-statistical-comparisons-correctly"),
      report("phase-g--definitive-evaluation-and-independent-audit"),
      foundations("connecting-the-completed-results-to-the-mathematics"),
    ],
  },
  {
    id: "h",
    title: "H · Service, profiles and manuscript",
    tag: "ENGINEERING / RESEARCH COMMUNICATION",
    why: "Research code must be inspectable, restartable and explainable. A working interface is useful, but must not manufacture scientific claims.",
    how: "Added FastAPI jobs, strict inputs, durable queue state, explicit fallback, tracing and a separate local dashboard. Checked actual CPU inference and restart persistence, profiled synchronized GPU embedding batches, assembled and visually reviewed a 13-page manuscript.",
    math: "Reported percentiles and throughput need denominators and workloads. GPU batching amortizes overhead, subject to memory. Five fictional service comparisons are not a production latency benchmark.",
    result:
      "The service uses the same research library and real local models. Saved outputs survive container recreation with their named state volume. The manuscript numerical sections derive from artifacts.",
    boundary:
      "No production deployment or prompt-injection guarantee is established. Continuous generation batching, a demo video and independent causal error annotation are absent. The guided website is a later presentation layer, not a new scientific run.",
    deep: [
      foundations("service-foundations--requests-jobs-and-observability"),
      report("phase-h--actual-service-persistence-and-batching-measurements"),
      foundations("turning-numerical-artifacts-into-a-manuscript"),
      ref("service", "", "Operational guide"),
    ],
  },
  {
    id: "i",
    title: "I · Release and remaining boundaries",
    tag: "ARTIFACT / EXTERNAL REVIEW",
    why: "A result needs enough preserved material for another person to inspect and reconstruct it. A repository release must not be confused with publication acceptance.",
    how: "Packaged source, wheel, manuscript PDF, checksums, compact predictions and frozen coefficient instances. Documented data/model restoration, upstream rights and outstanding author decisions.",
    math: "Checksums bind artifacts to bytes; reconstruction tolerances account for tiny numerical reduction differences, not changed predictions or IDs. A source snapshot and an environment lock preserve different inputs to a calculation.",
    result:
      "Saved statistical tables and recorded solver cases reconstruct. The original v0.1.0-research preview remains preserved. Current documentation and service revisions are distinguishable from the frozen scientific core.",
    boundary:
      "Independent scientific review, rights/licensing choices, actual authorship, venue formatting and submission remain external work. No acceptance, novelty certificate or hardware execution is inferred.",
    deep: [
      foundations("artifact-checks-and-independent-reconstruction"),
      foundations("versioned-release-versus-scientific-acceptance"),
      report("phase-i--reproducible-artifact-and-external-boundaries"),
      ref("handoff", "", "Final handoff"),
    ],
  },
];
const glossary = {
  RAG: "Retrieval augmented generation: supply retrieved source text to a generator so it can answer using external information.",
  Evidence:
    "Information that supports answering a particular question. Relevance alone does not establish support.",
  "Inference inputs":
    "Fields available to the deployed calculation: question, source text, identities and provenance. They exclude answer keys.",
  "Reference annotations / gold labels":
    "Expected answers and annotated supporting passages used for evaluation, not ordinary selection.",
  Corpus:
    "A collection of source documents searched before a candidate subset is selected.",
  Token:
    "A model-specific text unit. Token counts are not word counts and differ across tokenizers.",
  Chunking:
    "Split long documents into bounded, traceable units that fit the embedding encoder.",
  Embedding:
    "A learned numerical representation of text. It is not a list of verified facts.",
  "Cosine similarity":
    "Normalized vector dot product. Unit-vector dot product equals cosine, not a calibrated support probability.",
  "Lazy loading":
    "Load model weights when first needed rather than when the service process starts.",
  "Embedding cache":
    "Persist already computed vectors under keys identifying content and the representation recipe.",
  "Persistent index":
    "A saved searchable vector structure with consistent metadata so it can be restored across process restarts.",
  FAISS:
    "A vector-search library. This project uses exact inner-product chunk search with normalized vectors.",
  BM25: "Lexical retrieval using term rarity, term-frequency saturation and document-length normalization.",
  Reranker:
    "A more expensive question/passage joint model used to reorder candidate results.",
  MMR: "Maximal marginal relevance: choose relevant items while discouraging redundancy with already selected items.",
  QUBO: "Quadratic unconstrained binary optimization. Our native count/token problem is constrained; a penalty can encode count into a QUBO.",
  "ILP / MILP":
    "Integer / mixed-integer linear programming. Binary pair products are linearized with auxiliary variables and exact inequalities.",
  Objective:
    "A mathematical preference over selections. Minimizing it need not maximize generated-answer correctness.",
  "Dense formulation":
    "Many variable pairs have nonzero interactions. This can increase storage, optimization and compiled circuit work.",
  "Evidence modelling":
    "Turn question/source signals into estimated usefulness and complementarity features. The current entity-link proxy is not verified factual reasoning.",
  "Ising Hamiltonian":
    "A quantum operator with fields and pair couplings whose basis-state energies encode a binary objective.",
  QAOA: "A parameterized quantum cost/mixer circuit with a classical angle optimizer. Here its quantum evolution is classically simulated.",
  COBYLA:
    "Constrained Optimization BY Linear Approximation: a derivative-free optimizer used to adjust circuit angles.",
  Statevector:
    "The complex amplitudes describing a pure quantum state. Explicit simulation requires exponentially growing storage.",
  Shot: "One circuit measurement sample. Finite-shot sampling differs from reading an exact statevector distribution.",
  StatevectorSampler:
    "A Qiskit primitive that samples simulated quantum states. Used by the retired wrapper, not proof of QPU execution.",
  NumPyMinimumEigensolver:
    "A classical lowest-eigenvalue solver used by the retired exact wrapper; it is not a physical quantum processor.",
  MinimumEigenOptimizer:
    "A Qiskit adapter that maps supported optimization problems to operators and interprets solver output. The underlying solver can be classical.",
  "XY mixer":
    "An exchange-based circuit that preserves the number of selected bits ideally. Noise can break this property.",
  "Global phase":
    "A common unit-magnitude complex factor on the whole state; it cancels from measurement probabilities.",
  Sparsification:
    "Remove some pair interactions while retaining a declared budget and tracking the objective change.",
  Ablation:
    "Remove or change a component under controlled conditions to investigate what it contributes.",
  "Precision / recall":
    "Overlap divided by predicted items / reference items. Always specify whether the items are answer tokens or evidence documents.",
  "Recall@k":
    "Annotated relevant items recovered among the first k retrieved/selected items, under a declared identity and denominator.",
  F1: "Harmonic mean of precision and recall. Answer-token F1 and document-selection F1 evaluate different targets.",
  "Paired bootstrap":
    "Resample the same question IDs together across methods to quantify uncertainty in their mean difference.",
  Pilot:
    "A small preliminary run used to check feasibility, settings and variability before freezing the final experiment.",
  Profiling:
    "Measure where time, memory or other resources are used for a stated workload.",
  "Cold / cached run":
    "A cold run includes first-use loading/computation; a cached run can reuse existing state. Warm models and warm caches are different conditions.",
  "Pinned dependencies":
    "Software versions fixed for repeatable installation. They do not themselves prove scientific correctness.",
  Manifest:
    "Recorded settings plus actual identities and execution metadata for a run.",
  FastAPI:
    "A Python web API framework used here to validate requests and expose local inference jobs.",
  "GPU batching":
    "Process several embedding inputs together to amortize overhead, while respecting memory limits.",
  "Quantum advantage":
    "A demonstrated advantage under a clearly defined comparison with strong classical alternatives. Quantum involvement alone is insufficient.",
  Noninferiority:
    "Evidence that a method is not worse by more than a predeclared acceptable margin. A nonsignificant difference does not establish this.",
};
module.exports = { chapters, phases, glossary };
