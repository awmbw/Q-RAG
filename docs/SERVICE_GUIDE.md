# Local demonstration and API

The service calls the same retrieval, graph, selection and generation library as the experiments. It accepts source text and questions, not reference answers. It is a local demonstration with serialized inference, not a production multiuser deployment. The live laboratory is served at `/`, the complete project walkthrough at `/journey`, and interactive OpenAPI documentation at `/docs`.

## Complete project walkthrough

Open `/journey` to follow the problem, current state, original plan, foundations, research protocol, baseline and phases A–I, measured results, reproducibility, service and manuscript. Guided and deep modes include the full references inside the website. Search, a glossary, a phase explorer, numerical examples, saved-result charts and a literal JSON evidence viewer support the explanation. None of these controls submits inference jobs; model-cold readiness does not block reading.

The [journey guide](journey/README.md) documents content sources, navigation, development-only dependencies and rebuilding. The compiled bundle, equations, fonts and figures ship with the Python package; no external JavaScript/font CDN or Node runtime is needed by visitors. The result explorer reads public saved analyses, while clearly labelled examples calculate illustrative quantities in the browser. Quantum execution remains simulated, and the original research conclusions remain unchanged.

Functional, numerical, HTTP and packaging checks are recorded separately from visual review in the [journey verification receipt](research_report/evidence/journey_20261112.json). The available browser connection failed before navigation; actual desktop/mobile painting and browser interaction review remain unverified.

## Dashboard

The dashboard uses a paper background, a dotted grid, blue accents and local display/serif/monospace fonts, with visual inspiration from [AI Engineering from Scratch](https://aiengineeringfromscratch.com/). Its layout, diagram and application code are specific to Q-RAG. All fonts are served locally; their upstream license notices are in [the font directory](../src/qrag_service/static/fonts/README.md). The browser does not need an external font service.

Edit source titles and text in Cards mode, or use JSON mode to edit the complete source array, including IDs. Add/remove sources, set the shared count, choose selectors and press Compare methods. Reset example restores the fictional demonstration. Arrow keys switch editor tabs. The interface exposes model-cold, queued, running, completed and failed states. Changing inputs after a result marks the displayed answers as belonging to the previous comparison.

Each result shows its actual answer, supplied sources, context tokens, selection/generation time, objective, solver status and any classical fallback. Expand the source details to read the context supplied to the generator. Expand QAOA details to see feasible shots and complete compiled line costs. The graph includes a text disclosure of shared entities, so inspecting a link does not depend on hovering. At most 16 graph nodes are drawn in a large pool; the interface discloses that limit and lists all extracted links.

The headline dataset/question/record counts describe the frozen research study. They are not live service counters. The hero diagram is labeled illustrative. No new evidence-guidance or quantum-advantage claim is introduced by the redesign.

The current laptop demonstration remains at `http://127.0.0.1:8766/`. The redesigned container reuses the existing named state volume and read-only model mount. The stopped `qrag-release-demo-before-redesign` container is retained for rollback; do not run both containers against the same job database. Standard source/container installation below builds the current dashboard as part of the service.

### Frontend behavior checks

The small [DOM check script](../scripts/check_dashboard.cjs) runs application events with explicitly synthetic API responses. It needs Node and jsdom only for development verification; the dashboard itself has no Node build or runtime requirement.

```bash
npm install --prefix .cache/dashboard-checks --no-audit --no-fund jsdom@26.1.0
NODE_PATH="$PWD/.cache/dashboard-checks/node_modules" node scripts/check_dashboard.cjs
node --check src/qrag_service/static/dashboard.js
venv/bin/python -m pytest tests/test_service.py -q
```

The nine DOM checks cover source editing, JSON round trips, count limits, reset, validation, answer/source/circuit rendering, explicit fallback, text-only rendering of untrusted output, failure recovery and keyboard tabs. These checks do not render CSS or establish browser layout, accessibility certification or general injection resistance. The [redesign verification](research_report/evidence/dashboard_redesign_20261110.json) separately records real HTTP/model execution, asset hashes and the remaining browser-review limit.

## Run on the laptop

From the repository root with the tested environment and downloaded model snapshots:

```bash
venv/bin/python scripts/download_models.py --core-only
QRAG_TRACE_CONSOLE=1 venv/bin/uvicorn qrag_service.app:app \
  --host 127.0.0.1 --port 8000 --workers 1
```

The first job loads the frozen MiniLM and Qwen 1.5B snapshots. `/health` can succeed while `/ready` returns 503 because weights are not loaded. This is expected cold readiness, not a crashed application. The first job includes model preparation time. `QRAG_DEVICE=cpu` forces CPU; otherwise the local service uses CUDA when available. The GPU path uses float16 generation and the CPU path uses float32.

The service's `qaoa` option uses the frozen basis-start XY p=1 circuit. Its first cost phase is global; the prepared exploratory ansatz is currently a research control, not silently substituted into this API. See the [state-preparation derivation](TECHNICAL_FOUNDATIONS.md#sampling-state-preparation-and-a-weak-depth-one-circuit).

## Container

```bash
docker build -t qrag-research:local .
docker volume create qrag-service-state
docker run --rm --name qrag-demo -p 127.0.0.1:8000:8000 \
  --cpus=4 --memory=12g \
  -e QRAG_TRACE_CONSOLE=1 \
  --mount type=volume,src=qrag-service-state,dst=/app/.cache \
  --mount type=bind,src="$HOME/.cache/huggingface/hub",dst=/home/app/.cache/huggingface/hub,readonly \
  qrag-research:local
```

The image uses CPU PyTorch, runs as a nonroot user, contains no model weights and resolves models offline through the read-only mount. The named volume holds caches, indexes and job state. It is separate from the weight cache. The image build needs network access to public package repositories. `WITH_MODELS=0` builds the lighter import/HTTP CI image; it cannot execute real model inference without the omitted packages.

The observed CPU runtime is pinned in [requirements-container.lock](../requirements-container.lock); the lighter HTTP/tracing closure is in [requirements-container-service.lock](../requirements-container-service.lock). CPU Torch is pinned separately and fetched from the official PyTorch CPU index. These CPU package versions differ from the CUDA research host, whose exact snapshot is [requirements-laptop.lock](../requirements-laptop.lock). The container verifies service portability; it is not claimed to be a bit-identical GPU research environment.

## Endpoints and meanings

| Request | Result |
| --- | --- |
| `GET /journey` | Model-free project walkthrough with locally served references and saved results |
| `GET /health` | Process can answer requests; states that quantum hardware is false |
| `GET /ready` | 200 when models are ready; otherwise 503 with a cold-state description |
| `POST /jobs` | Validate a supplied-pool comparison and return 202 with a job ID |
| `GET /jobs/{id}` | Poll queued/running/completed/failed/timed_out/interrupted state and results |
| `POST /corpora` | Submit persistent corpus ingestion as a bounded background job |
| `POST /query` | Retrieve from an ingested corpus and compare selectors |
| `GET /metrics` | JSON queue/job/timing counters, not a Prometheus text endpoint |

An example comparison request is:

```json
{
  "question": "In which country was the director of Film A born?",
  "sources": [
    {"id": "a", "title": "Film A", "text": "Film A was directed by Maya Rao."},
    {"id": "b", "title": "Maya Rao", "text": "Maya Rao was born in India."},
    {"id": "c", "title": "Film release", "text": "Film A was released in 1995."}
  ],
  "methods": ["relevance", "milp", "qaoa"],
  "k": 2,
  "allow_classical_fallback": true,
  "deadline_seconds": 120
}
```

The response's `status_url` identifies the polling endpoint. A 202 response means accepted, not successfully answered. Results include the requested and actual method, supplied source IDs, generated text, context/input/output tokens, stage costs and simulation resources. Supplied IDs identify the context given to the model; they do not prove the answer is supported by every listed source.

Corpus ingestion uses `{"corpus":"demo","sources":[...]}`. A subsequent query uses `{"corpus":"demo","question":"...","candidates":20,"k":3,"retrieval":"hybrid","methods":["relevance","milp"]}`. Corpus names are restricted identifiers, not filesystem paths. Hybrid retrieval uses BM25 and exact dense chunk search with rank fusion.

## Resource and failure policy

There is one inference worker and capacity for four outstanding jobs. A full queue returns 429 and a retry hint. Unknown JSON fields, duplicate source IDs, invalid k and size-limit violations return 422. Input limits are declared in [schemas.py](../src/qrag_service/schemas.py): at most 100 comparison sources, 12,000 characters per source, 100,000 combined comparison characters, and up to 500 sources/one million characters for ingestion. The generation limit is 32 new tokens.

If a request includes QAOA and more than ten sources, all its compared selectors use the same label-independent relevance-reduced top-ten pool. This policy is exposed in results. It avoids comparing different candidate opportunities. Requests without QAOA can use the larger validated pool.

A permitted classical fallback is explicitly labeled with its reason and actual method. It is a service reliability behavior, not a successful QAOA research execution. Deadlines are checked between bounded stages; they do not forcibly preempt an ongoing tensor operation. Restarted abandoned jobs become interrupted. Terminal job retention is bounded at 200 entries. The SQLite store is protected against accidentally starting multiple inference workers against it.

Sources are untrusted text. The source-only prompt is a request to the model, not a proof of injection resistance or groundedness. The service has no authentication, public deployment hardening or arbitrary remote-source fetching. Keep the documented loopback binding for the local demonstration.

## Verification and observability

The integration script is [benchmark_service.py](../scripts/benchmark_service.py). It checks actual HTTP ingestion, repeated comparisons including simulated QAOA, cache reuse and corpus retrieval using fictional sources. Its five repeated requests provide a scoped p50/p95, not a production latency estimate. The separate untrusted-source diagnostic is one fixture, not a security benchmark.

`QRAG_TRACE_CONSOLE=1` emits OpenTelemetry preparation/retrieval/embedding/graph/selection/generation spans into local logs. Structured completion records omit source text. Full job responses and the local SQLite database still contain answers and supplied sources, so use non-sensitive demonstration material. A functional HTTP check and a visual browser review are different checks; no visual review is claimed when no browser surface is available.
