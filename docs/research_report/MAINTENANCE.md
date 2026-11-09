# Research documentation maintenance

Maintain three connected documents after each completed phase, meaningful experiment or technical review:

| Document | Update responsibility |
| --- | --- |
| docs/RESEARCH_PROGRESS_REPORT.md | Concise objective state of implementation, principal math, verified results and limitations |
| docs/TECHNICAL_FOUNDATIONS.md | Concept explanations, assumptions, derivations, worked examples, code mapping and failure cases |
| docs/DEVELOPMENT_SEQUENCE.md | Dependency order, implementation reasons, verification evidence and remaining phases |

Use docs/README.md as the navigation entry point. Keep the progress report objective and audience-neutral. Exclude intended-reader references, personal objectives or assessments, feedback requests, meeting notes and maintenance instructions from the report. Preserve detailed traces in experiment artifacts.

**At every phase boundary**

1. Record the date, completed scope, source revision or fingerprint, and remaining limitations. Update the implementation-status table based on code and verification rather than the scheduled milestone date.
2. Update the report's principal formulation to match the implementation, and add detailed derivations to the technical companion. For each new component, explain its problem, prerequisites, symbols and assumptions, a worked calculation, source mapping, alternative decisions, verification and downstream effect. Distinguish implemented terms from planned extensions.
3. Add each new experiment's dataset and split, frozen question IDs, sample size, model revisions, budget, hyperparameters, seeds, execution mode and error policy.
4. Recompute reported metrics from question-level records. Check feasibility and objective values independently. Preserve failed questions in the stated denominator and label successful-only summaries.
5. Save an evidence snapshot alongside the report with hashes and per-question outcomes. Preserve the full local artifacts separately because results/ is ignored by Git. Do not put model weights or full datasets into this directory.
6. Record interpretations, counterexamples, limitations and changed decisions. Keep unfavorable results. A different objective, budget or dataset split starts a new comparison rather than silently replacing the old one.
7. Update the development sequence with what changed, why and which artifact verifies it. Mark formal phases complete only when their acceptance criteria are met; a working slice can span partial phases.
8. Increment document versions and preserve changes in version control. Create dated exports when an export tool is available; Markdown sources and run artifacts remain authoritative. Keep process notes here rather than in the report.
9. Check cross-links, symbols, matrix dimensions and numerical examples. Executing an illustrative example does not create a new model-evaluation result. Do not copy illustrative scores into benchmark tables.
10. Keep any individual answers or mastery assessments in the existing separate learning log. Explanations and published solutions are not evidence of independent understanding.

**Before sharing the report**

- Open the report in a Markdown preview with math enabled and inspect equations, tables and links.
- Confirm the report date is distinct from the experiment date.
- Check every numerical table against its evidence snapshot and state whether it is a pilot or final evaluation.
- Keep formulation improvements separate from solver improvements.
- State whether quantum results are simulated, noisy or hardware-based. Classical MILP results must not be labeled quantum results.
- Exclude audience-specific commentary, requests for feedback and meeting-related content.

**Baseline evidence**

The compact baseline_dev_001.json snapshot was audited on November 9 2026 against the November 4 run. It includes six successful method/question records and the recorded dataset/package hashes. It is supporting evidence, not a portable reproduction of the entire model environment.

The public snapshot uses model identifiers and immutable revisions in place of machine-specific cache paths. Its artifact hashes refer to the unchanged original local run files. This publication-only transformation does not alter predictions, metrics, timings or the original artifacts.

**Version control at phase boundaries**

Commit source changes, relevant tests, experiment configurations, dependency specifications, updated documentation and compact verified evidence. Preserve unsuccessful results and state incomplete acceptance criteria. Use focused commits during implementation and a documented milestone when the phase's acceptance criteria are met.

Keep downloaded datasets, model weights, indexes, caches and bulk run outputs outside Git. Commit the preparation procedures, provenance, checksums and index/cache configuration needed to recreate them. Archive substantial final experiment bundles separately and record their location and checksums. Review the staged file list before committing; locally excluded material must remain local.

The mathematical code and real experiment were not changed while preparing this report. Seventeen offline correctness tests were rerun successfully. Word export was not generated because this session does not expose the managed document-export runtime; no unverified Word or PDF file is presented as complete.
