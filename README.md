# Q-RAG: research on context selection for RAG

Q-RAG investigates how mathematical optimization and quantum algorithms can select useful context for multi-hop question answering. The current research foundation compares relevance ranking with a constrained classical MILP, generates actual answers, and records answer quality separately from document-selection metrics.

This is research in progress. The existing experiments do not establish quantum advantage. A QAOA wrapper exists in the legacy code; the new baseline runner currently uses classical methods. See the [implementation plan](docs/IMPLEMENTATION_PLAN.md) for the proposed graph and quantum experiments.

The [research progress report](docs/RESEARCH_PROGRESS_REPORT.md) records the mathematical formulation, implementation status, audited results and research decisions. Update it at each phase boundary using the [report maintenance checklist](docs/research_report/MAINTENANCE.md).

The [technical companion](docs/TECHNICAL_FOUNDATIONS.md) explains concepts, derivations and worked examples. The [development sequence](docs/DEVELOPMENT_SEQUENCE.md) connects those concepts to the implementation order and decisions. See the [documentation index](docs/README.md) for the full set.

## Run the first baseline

From the repository root, using the existing environment:

```bash
venv/bin/python -m pip install --no-deps --no-build-isolation -e .
venv/bin/python -m unittest discover -s tests -v
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false venv/bin/python -m qrag.experiments.run \
  --config configs/dev_baselines.toml --output results/my_baseline_run
```

The provided configuration uses the first three **development** questions, exactly five passages per method, and locally cached, revision-pinned MiniLM and Qwen weights. For pools smaller than five, the explicit `use_all` policy uses all candidates for both methods. A fresh output directory is required unless `--resume` is supplied. Model weights and processed data are not bundled with the repository.

For a fresh environment, install the core with `requirements-baselines.lock` and the package with its `models` extra. The core lock covers NumPy/SciPy; model-runtime versions are recorded in each manifest, rather than supplied as a portable full-environment lock. See the [baseline guide](docs/BASELINE_GUIDE.md) for prerequisites and limitations.

## What is implemented

- Separate inference inputs and evaluation labels.
- A common relevance–redundancy objective, with native exact-count constraints.
- Stable relevance top-k and MILP, with solver status, bounds and independent feasibility checks.
- HotpotQA-compatible answer EM/token F1 and document-level supporting-evidence metrics.
- Shared per-question embeddings, consistent context ordering and deterministic decoding settings.
- Explicit errors for overlong embedding inputs and overlong generation prompts.
- Manifests, per-question predictions, aggregate summaries, failure reporting and guarded resume.
- Offline correctness tests and a CI workflow that does not download models.

Each completed output directory contains `manifest.json`, `predictions.jsonl` and `summary.json`. Run-level failures after artifact-store creation also produce `failure.json`; earlier configuration, data or model-resolution failures may only produce a CLI error. Answer averages retain failed questions in the denominator. Evidence and token averages are explicitly labeled as successful-only.

## Research interpretation

Equal passage counts do not imply equal token counts. The first runner isolates passage-count differences; a token-budget experiment is a later milestone. Better QUBO energy does not imply better answers. Dropping nonpositive similarity terms alone does not establish useful quantum circuit savings.

The legacy `notebooks/` scripts remain available. Their recall/F1 figures concern document selection, their main optimization experiments use the classical exact solver, and their unequal context sizes cannot establish answer-quality or quantum improvements. The new runner provides the controlled starting point for subsequent studies.

The [first-session notes](docs/FIRST_BASELINE_SESSION.md) record the actual smoke-run results and data-quality observations. Three development questions validate execution, not scientific superiority.
