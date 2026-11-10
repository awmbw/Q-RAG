# Project documentation

| Document | Purpose |
| --- | --- |
| [Research progress report](RESEARCH_PROGRESS_REPORT.md) | Objective account of implemented methods, measured results, mathematical formulation, limitations and phase progress |
| [Technical foundations and implementation notes](TECHNICAL_FOUNDATIONS.md) | Detailed concepts, derivations, numerical examples, code mapping and technical review questions |
| [Development sequence](DEVELOPMENT_SEQUENCE.md) | Dependency order, reasons for implementation decisions and completed versus remaining phases |
| [Historical baseline execution guide](BASELINE_GUIDE.md) | Preserved first-run commands and baseline-specific runtime boundaries |
| [Implementation plan](IMPLEMENTATION_PLAN.md) | Detailed research and engineering backlog |
| [Experiment protocol](EXPERIMENT_PROTOCOL.md) | Frozen hypotheses/controls, failure policy and declared exploratory extensions |
| [Literature comparison](LITERATURE_REVIEW.md) | Primary-source overlap, reproduction boundaries and bounded novelty assessment |
| [Reproducibility](REPRODUCIBILITY.md) | Environment choices, input/model restoration, inference and saved-prediction reconstruction |
| [Service guide](SERVICE_GUIDE.md) | Local dashboard, API, container, queue, observability and reliability limits |
| [Publication guide](PUBLICATION_GUIDE.md) | Checked venue routes, timeline choices and remaining author decisions |
| [Rights and attribution](RIGHTS_AND_ATTRIBUTION.md) | Upstream dataset/model terms and release boundaries |
| [Claim-to-evidence map](CLAIM_EVIDENCE_MAP.md) | Exact artifacts supporting each measured or mathematical statement |
| [Remaining external work](HUMAN_HANDOFF.md) | Human review, authorship, rights, annotation, browser review and submission |
| [Manuscript](../paper/manuscript.md) | Editable research paper with regenerated numerical sections |
| [Reviewed PDF](../output/pdf/manuscript.pdf) | Thirteen-page rendered manuscript; all pages visually inspected |
| [Derived result tables](../paper/results/) | Generated analyses and figures' numerical inputs |
| [Unjudged graph review sample](research_report/annotation_sample.json) | Source-grounded development worksheet; not measured semantic graph accuracy |
| [First baseline results](RESEARCH_PROGRESS_REPORT.md#verified-development-experiment) | Consolidated November 4 experiment, controls and interpretation |
| [Evidence snapshot](research_report/evidence/baseline_dev_001.json) | Versionable configuration and question-level outcomes behind the reported baseline |

The progress report gives the current state. The technical companion follows the pipeline in depth; the development sequence explains how the components were assembled. Experimental results belong to their recorded runs, while worked numerical examples are explicitly illustrative.

Superseded planning/session notes and the original prototype are available in the [preserved research release](https://github.com/awmbw/Q-RAG/tree/v0.1.0-research). The implementation plan supersedes the initial roadmap. The current checkout keeps one maintained report, foundations companion and development sequence rather than separate copies of the same baseline account.

At each phase boundary, use the [documentation maintenance checklist](research_report/MAINTENANCE.md) to align these documents. Separate implemented behavior, general mathematical background and proposed work.
