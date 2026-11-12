# Q-RAG: research on context selection for RAG

Q-RAG studies how classical optimization and simulated quantum algorithms select context for multi-hop question answering. It combines token-safe retrieval, an entity-link scoring proxy, constrained subset selection, sparse QAOA circuits and real local language-model answer evaluation.

The completed local study is an encoding-aware empirical comparison: **53,230 audited records across 24 conditions**, covering 1,000 distinct held-out questions, two generators and separately scoped controls. All quantum execution is classical simulation. The proposed evidence-guidance benefit is not established, and no practical quantum advantage is claimed. Read the [manuscript PDF](output/pdf/manuscript.pdf), [claim/evidence map](docs/CLAIM_EVIDENCE_MAP.md) and [remaining external work](docs/HUMAN_HANDOFF.md).

The [research progress report](docs/RESEARCH_PROGRESS_REPORT.md) records the mathematical formulation, implementation status, audited results and research decisions. Update it at each phase boundary using the [report maintenance checklist](docs/research_report/MAINTENANCE.md).

The [technical companion](docs/TECHNICAL_FOUNDATIONS.md) explains concepts, derivations and worked examples. The [development sequence](docs/DEVELOPMENT_SEQUENCE.md) connects those concepts to the implementation order and decisions. See the [documentation index](docs/README.md) for the full set.

## Start here

The website now includes a complete **project journey** at `/journey`: ten connected chapters, the historical baseline and phases A–I, interactive mathematical examples, saved-result comparisons, the full manuscript and an in-site reference library. Follow the guided flow or expand the full derivations. The existing live comparison laboratory remains at `/`. Reading the journey does not load models or start inference. See the [journey build guide](docs/journey/README.md).

From the repository root, using the existing laptop environment:

```bash
venv/bin/python -m unittest discover -s tests -v
venv/bin/python scripts/download_models.py --core-only
venv/bin/uvicorn qrag_service.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Open the project journey at `http://127.0.0.1:8000/journey` or the live laboratory at `http://127.0.0.1:8000`. Only a submitted inference job needs the pinned local MiniLM and Qwen 1.5B weights. Cold readiness returns 503 until loading succeeds; the reading website remains usable. API inputs contain no reference answers. The [service guide](docs/SERVICE_GUIDE.md) explains the API, container, queue, limits and explicit fallback policy.

For a fresh installation, input restoration and model-free result reconstruction, follow [reproducibility](docs/REPRODUCIBILITY.md). Weights and datasets are not bundled. CPU container, CI and CUDA laptop dependencies have distinct recorded snapshots. The [historical baseline guide](docs/BASELINE_GUIDE.md) documents the original three-question experiment rather than the complete current study.

## What is implemented

- Sentence-aware token-safe chunks, source offsets, content-addressed embedding/graph caches and checked FAISS/SQLite indexes.
- Dense, BM25, hybrid, cross-encoder, MMR, coverage, greedy, MILP, annealing and uniform feasible-sampling references.
- Common relevance/redundancy/entity-link coefficients, native count/token constraints and certified solver-status accounting.
- Signed sparsification with absolute, random, degree and evidence-guided edge rules; original and surrogate energies retained.
- Actual Qiskit statevector/shot/noise diagnostics, penalty/XY encodings and complete synthetic-target compilation.
- Explicit diagnosis of the basis-start depth-one global-phase limitation, plus a separately labeled feasible-preparation control.
- HotpotQA/MuSiQue answer EM/F1, supporting-document metrics, question-level paired intervals and failure-inclusive answer denominators.
- Pinned MiniLM/Qwen revisions, actual prompts/token IDs, frozen split/corpus manifests, journal recovery and source snapshots.
- FastAPI jobs, persistence, local dashboard, OpenTelemetry stage traces, a nonroot CPU container and remote correctness/build CI.

Each main study output contains a manifest, append-only predictions journal, summary and scientific source snapshot. The [primary matrix](configs/final_matrix.json) fixes 18 conditions and 50,290 method/question evaluations over 1,000 distinct held-out questions. Solver seeds, methods and generator repeats are not additional independent questions. Secondary controls have separate scopes and manifests.

## Research interpretation

Equal passage counts do not imply equal tokens; equal caps do not imply equal consumption. Better objective energy does not imply better answers. A squared count penalty can make a sparse cost graph dense again. Count-preserving mixing has preparation and mixer costs, and a basis-start first diagonal cost layer is only a global phase. Complete compiler measurements are not minimum-cost proofs or hardware speedups.

The original prototype and its document-selection notebooks were retired from the current checkout after verifying that the current package/tests do not depend on them. Their code remains in the [preserved research release](https://github.com/awmbw/Q-RAG/tree/v0.1.0-research). Their recall/F1 figures concern document selection and unequal context sizes; they cannot establish answer-quality or quantum improvements. The historical first baseline is documented in the [progress report](docs/RESEARCH_PROGRESS_REPORT.md#verified-development-experiment), while the current runner provides the controlled study implementation.

The [manuscript source](paper/manuscript.md) separates principal and exploratory comparisons. The [publication guide](docs/PUBLICATION_GUIDE.md) records current venue options and the remaining author/submission decisions. [Rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md) identify upstream terms; a project-wide license has not been invented on the owners' behalf. No scholarly submission or acceptance is claimed.

For an inexpensive artifact check after installing the CPU CI dependencies, run:

```bash
venv/bin/python scripts/reproduce_public_tables.py --verify
venv/bin/python scripts/reproduce_quantum_instance.py --verify-recorded
```

These commands reconstruct saved statistics and rerun one frozen solver instance without model weights or dataset downloads. The released coefficient bundle contains 110 optimization instances. Full end-to-end inference is a separate, more expensive reproduction route described in the guide.
