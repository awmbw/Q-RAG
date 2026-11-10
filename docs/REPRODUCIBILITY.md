# Reproduce the study and inspect its artifacts

The project offers two different checks: regenerate statistics from saved predictions, or repeat model/solver inference from restored inputs. The first is inexpensive and does not validate model behavior independently. The second needs the recorded weights, data and compute. Keep that distinction when reporting reproduction.

## Environments

The measured research host uses Linux x86-64, Python 3.14, an RTX 5060 Laptop GPU with approximately 7.53 GiB of PyTorch-visible memory, and about 22 GiB host RAM. The two generators fit sequentially; do not load both alongside competing GPU jobs. Models run in inference mode, without fine-tuning or a paid API.

- [requirements-laptop.lock](../requirements-laptop.lock): exact observed host environment, including CUDA-specific wheels. It is not a portable CPU installation recipe. CUDA Torch is fetched from its matching official PyTorch index.
- [requirements-ci.txt](../requirements-ci.txt): the lighter tested correctness/lint/build environment without model downloads.
- [requirements-container.lock](../requirements-container.lock): observed CPU demonstration environment; CPU Torch is installed separately from the official CPU index by [Dockerfile](../Dockerfile).
- [requirements-baselines.lock](../requirements-baselines.lock): small historical NumPy/SciPy baseline environment.

For a fresh CPU correctness environment:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-ci.txt
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m unittest discover -s tests -v
```

The full CI environment includes Qiskit and exercises the actual circuit tests. The minimal baseline environment explicitly skips unavailable optional integrations. No fake backend is used for scientific results; test doubles are confined to orchestration/service tests.

## Restore exact inputs

From a fresh working tree with the research dependencies installed:

```bash
venv/bin/python -m pip install -e '.[models,research,service,dev,publishing]'
venv/bin/python scripts/download_models.py
venv/bin/python scripts/restore_splits.py
venv/bin/python scripts/restore_corpus_candidates.py
```

The extras command resolves dependencies and is a convenience installation, not an exact environment recreation. Use the tested environment snapshots for exact versions. [Model revisions](../configs/model_revisions.json) and every final configuration fix immutable snapshots. Download scripts obtain public artifacts from their original hosts; they do not enable remote model code. The MuSiQue archive is approximately 272 MB, and all weights/data require additional disk space. There is no cloud or QPU prerequisite.

The split restorer checks the official MuSiQue archive hash and reconstructs rows in frozen ID order from pinned HotpotQA sources and the official MuSiQue archive. Existing different files are rejected. The corpus restorer uses saved retrieved IDs and profile values to reconstruct the six exact candidate files without rerunning embedding search. All four split and six corpus-file hashes were independently reconstructed during this run.

Restoring frozen candidate files verifies selection inputs. To rerun candidate retrieval itself, [prepare_corpus_experiment.py](../scripts/prepare_corpus_experiment.py) builds checked FAISS/SQLite indexes and records dense/BM25 rank-fusion profiles. It is a separate expensive operation and can expose numeric/platform ordering differences; never silently replace frozen pools in a primary solver comparison.

## Full inference

The [protocol](EXPERIMENT_PROTOCOL.md) explains principal comparisons, failure policy and changes. The [primary matrix](../configs/final_matrix.json) checks each configuration's SHA-256 before starting sequential runs:

```bash
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false \
  venv/bin/python scripts/run_matrix.py --matrix configs/final_matrix.json
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false \
  venv/bin/python scripts/complete_evaluation.py
```

The completion driver requires all 18 primary conditions to be complete, then runs the formulation control, complete-gate-cap diagnostic, exploratory preparation control, artifact audits and assembly. `--wait-for-primary` is for a separately running primary controller; do not launch duplicate controllers or writers. Per-run logs are under the ignored root results directory. It can be normal for a completed scientific run to contain explicit failures; a successful process exit alone is insufficient to establish a complete question/method grid.

Primary records total 50,290 method/question evaluations over 1,000 distinct held-out questions. Repeated methods, seeds and generator conditions are not additional independent questions. Secondary controls have separate manifests and sample sizes. Exact-expectation simulator training, finite-shot training and artificial final-sampling noise have different resource meanings.

The preparation extension has its own source snapshot and composite identity because it changes the circuit without changing the frozen primary core. It is post-freeze exploratory. The original basis-start circuit and Unicode-provenance cycle-one archive are retained and clearly distinguished from definitive cycle two.

For an independent rerun alongside existing outputs, use a fresh checkout/output tree. Never delete existing scientific artifacts to make resume accept changed settings. Resume requires matching code/config/data/environment identities and protects successful results. Single-condition commands are available through `python -m qrag.experiments.study --help`; a new result directory is the safest choice when changing an experiment.

## Saved-prediction reconstruction

After final evidence is exported:

```bash
venv/bin/python scripts/reproduce_public_tables.py --verify
```

This verifies compressed-prediction hashes and regenerates method tables and paired intervals without model weights or dataset text.

The released [optimization fixture manifest](research_report/evidence/quantum_instances_manifest.json) additionally identifies 110 fixed coefficient arrays. To reproduce original, prepared or sparse solver cases without an encoder or LLM:

```bash
venv/bin/python scripts/reproduce_quantum_instance.py --verify-recorded
venv/bin/python scripts/reproduce_quantum_instance.py --prepared --verify-recorded
venv/bin/python scripts/reproduce_quantum_instance.py \
  --run final_musique_quantum --sparsifier evidence --verify-recorded
```

The first frozen question is used unless an ID is supplied. The command checks the fixture hash and frozen source identity, runs actual Qiskit and MILP, and can compare selected indices, full energy and compiled gates with the recorded case. Exact recorded checks were verified in the pinned laptop environment; seeds and version pins do not guarantee identical variational trajectories on arbitrary machines. The normal result records still expose feasibility, energies and resources when exact verification is not requested.

For full local result assembly, use:

```bash
venv/bin/python scripts/audit_final_runs.py
venv/bin/python scripts/error_analysis.py
venv/bin/python scripts/assemble_results.py
venv/bin/python scripts/analyze_sampling_coverage.py
venv/bin/python scripts/build_architecture_figure.py
venv/bin/python scripts/export_quantum_instances.py
venv/bin/python scripts/reproduce_public_tables.py --verify
venv/bin/python scripts/build_paper_pdf.py
```

The auditor uses local full artifacts and pinned tokenizers. It recomputes scores, selected source membership, objective/surrogate energies, budgets and exact prompt token IDs. The report assembler requires complete grids and retains failed questions as zero answer scores. Completed zero-feasible circuits remain in circuit feasibility/resource means; unmeasured resources are not invented zeros. The sampling analyzer reads its saved development-only numerical evidence.

PDF rendering uses ReportLab with system Liberation Serif fonts and Matplotlib equation rendering. The final export must also be rendered and visually inspected with Poppler; a successful PDF write alone is not visual QA. See the manuscript's accompanying evidence for the actual completed checks rather than inferring success from available commands.

## What is public and what remains local

Public: implementation, configurations, frozen IDs/hashes, compact question-level predictions, statistics, figures, manuscript source, documentation and CI. Local: raw/processed data, weights, caches, large full predictions with source text/prompts/input IDs, superseded execution archives and temporary document renders. The rights boundary is documented in [attribution](RIGHTS_AND_ATTRIBUTION.md).

Compact exports preserve the hashes of original local artifacts. Their availability does not mean every large original file is included in Git. Restorers and the frozen source/configurations support the full inference route. Git commit identity, code snapshots and recorded runtime settings should accompany any later reproduction or revised experiment.

The versioned artifact builder requires a clean committed working tree and an already built wheel. `venv/bin/python scripts/build_release_bundle.py` checks public evidence/PDF identities, archives only tracked source material and creates checksums under the ignored local release directory. It excludes private notes, raw/processed data and weights. See [the handoff](HUMAN_HANDOFF.md) for rights-holder and submission decisions that remain outside the local run.
