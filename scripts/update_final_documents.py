"""Refresh bounded numerical report blocks from completed audited artifacts."""

import json
from pathlib import Path

from qrag.experiments.artifacts import atomic_text


def block(text, name, content):
    start, end = f"<!-- BEGIN {name} -->", f"<!-- END {name} -->"
    if start in text:
        before, remainder = text.split(start, 1)
        _, after = remainder.split(end, 1)
        return before + start + "\n" + content + "\n" + end + after
    return text.rstrip() + "\n\n" + start + "\n" + content + "\n" + end + "\n"


def main():
    evidence = Path("docs/research_report/evidence")
    audit = json.loads((evidence / "final_audit.json").read_text())
    assert audit["total_latest_records"] == 53230 and len(audit["runs"]) == 24
    overview = json.loads(Path("paper/results/overview.json").read_text())
    assert len(overview["runs"]) == 24
    service = json.loads((evidence / "service_benchmark.json").read_text())
    operation = json.loads(
        (evidence / "service_operational_verification.json").read_text()
    )
    assert operation["job_result_preserved_exactly"]
    assert operation["persistent_corpus_query"]["status"] == "completed"
    batch = json.loads((evidence / "embedding_batch_profile.json").read_text())
    results = (
        Path("paper/results/main_results.md")
        .read_text()
        .replace("](../figures/", "](../paper/figures/")
    )
    lines = [
        "## Phase G — definitive evaluation and independent audit",
        "",
        "The 18-condition definitive primary matrix is complete: **50,290 method/question evaluations over 1,000 distinct held-out questions**. Separate controls add 800 formulation, 140 gate-cap and 2,000 prepared-circuit records, giving **53,230 records across 24 completed runs**. All 24 grids were audited. The primary and formulation runs share the same frozen core source fingerprint; the preparation control adds an explicitly hashed extension. Documentation and service commits changed during execution, so a common scientific source hash is more precise than claiming one repository commit for every run.",
        "",
        "The audit recomputed dataset-specific scores, checked IDs/counts/token budgets, summed full and sparse energies independently, verified source/config/data identities and retokenized saved prompts. It independently counted feasible shots from measured bit strings, including failed circuits. The gate diagnostic's retained masks and final complete line circuits were reconstructed and recompiled. Its successful circuits satisfy the 180-gate cap. [Audit evidence](research_report/evidence/final_audit.json) records every checked condition.",
        "",
        "There is one genuine no-feasible-sample failure in the primary matrix: HotpotQA question `5add9bfa5542990dbb2f7e85`, penalty-full seed 42. It remains zero in answer averages and zero in completed-circuit feasibility. Twenty additional gate-cap control records reject the penalty encoding because no tested retention level fits the cap; they are explicit diagnostic failures rather than successful substituted executions. No service fallback enters scientific results.",
        "",
        "### Findings and interpretation",
        "",
        "The principal half-edge comparison does **not establish an evidence-guidance benefit** on either dataset. Both intervals include zero, so neither equality nor noninferiority follows. Lexical coverage has the highest observed F1 in all four 500-question classical count conditions. Graph-minus-base effects vary across settings and their reported exploratory intervals also include zero. These results support a bounded comparative/negative-result account, not a new state-of-the-art or quantum-advantage claim.",
        "",
        results,
        "",
        "### Complete result index",
        "",
        "Each linked analysis includes every method in that condition, answer/evidence/token outcomes, failures and paired intervals. Its JSON companion additionally retains resource and certification diagnostics. The public compact prediction file is identified and checksummed by the matching evidence manifest.",
        "",
        "| Condition | Method/question records | Analysis | Public evidence manifest |",
        "| --- | ---: | --- | --- |",
    ]
    for stem in sorted(overview["runs"]):
        count = audit["runs"][stem]["records"]
        lines.append(
            f"| {stem} | {count:,} | [complete table](../paper/results/{stem}_analysis.md) | [manifest](research_report/evidence/{stem}.json) |"
        )
    lines += [
        "",
        "### What can be reproduced without a model",
        "",
        "All 24 public prediction tables and their paired intervals reconstruct without loading an LLM or raw dataset. An additional [110-instance coefficient bundle](research_report/evidence/quantum_instances_manifest.json) supports solver-only experiments over 100 distinct quantum-subset questions and nested 12/16-candidate sensitivities. It contains no answer/support labels or source text. Four actual solver reproductions match recorded selected indices, full energy and compiled line gates: original full XY, prepared full XY, evidence-sparse XY and a 16-candidate case. [Reproduction checks](research_report/evidence/quantum_reproduction_smokes.json) document the scope.",
        "",
        "The exact [core source snapshot](research_report/evidence/scientific_source_snapshot.json) and [preparation extension snapshots](research_report/evidence/preparation_extension_snapshots.json) are released alongside configurations. Full prompts/input IDs remain in the large local run bundles; public restorers rebuild the frozen inputs from primary hosts. Model-free table regeneration is not an independent rerun of answer generation.",
        "",
        "The [error-signature analysis](../paper/results/error_analysis.md) includes deterministic examples of better common objective values with worse answers. These observations explain why optimizing a proxy does not certify useful evidence. They are not independently annotated causal error labels. Source overlap, imperfect references, weak entity links, a small quantum subset, one generator family and ideal statevector training remain limits.",
    ]
    report_path = Path("docs/RESEARCH_PROGRESS_REPORT.md")
    report = report_path.read_text()
    report = report.replace(
        "The frozen definitive evaluation is running. Final comparisons will be inserted only after its artifacts pass independent checks.",
        "The definitive evaluation and all declared controls are complete, and their 53,230 records pass the final artifact audit. The manuscript and release package report unfavorable findings as well as measured resource changes.",
    )
    report = report.replace(
        "| G frozen evaluation | Running | 18 primary conditions plus separately identified controls; statistical assembly follows completed runs |",
        "| G frozen evaluation | Complete | 18 primary conditions and six separately scoped control runs; 53,230 records audited and public statistics reconstructed |",
    )
    report = report.replace(
        "| H manuscript and demonstration | In progress | Editable manuscript, figure tooling, API/dashboard, tests and working container; final results and real-model HTTP benchmark pending |",
        "| H manuscript and demonstration | Complete within local scope | Numerical manuscript, 13-page visually checked PDF, real-model API/container checks, persistence and batch profiling; browser review remains unavailable |",
    )
    report = report.replace("preregistered comparison", "predeclared comparison")
    report = block(report, "DEFINITIVE_RESULTS", "\n".join(lines))
    b = batch["median_by_batch"]
    service_text = "\n".join(
        [
            "## Phase H — actual service, persistence and batching measurements",
            "",
            f"The locked nonroot CPU container completed real model ingestion and inference. Cold ingestion including preparation took {service['ingestion']['total_seconds']:.2f} seconds. Five model-ready fictional requests each compared relevance, MILP and simulated QAOA; all three returned India. Their measured comparison-request p50/p95 were **{service['model_ready_seconds_p50']:.3f}/{service['model_ready_seconds_p95']:.3f} seconds**. These are five repeated requests on one fictional workload, not dataset accuracy, isolated production throughput or a latency guarantee. CPU artifact audits ran during parts of these integration checks.",
            "",
            "Document/query embedding cache hits increased across requests, and graph cache hits appeared after the first identical comparison. A persistent corpus query returned four candidates and completed generation. The container was then recreated with the same named state volume: a completed job's full response remained exactly equal, cold readiness returned again, and the stored corpus successfully answered another query after model preparation. Actual local stage spans were captured. [Service measurements](research_report/evidence/service_benchmark.json) and [operational verification](research_report/evidence/service_operational_verification.json) retain the details.",
            "",
            "The untrusted-source input fixture returned India, but the selector supplied only the two normal evidence sources. It therefore does not test whether the generator resists an instruction that actually reaches its context. No prompt-injection resistance is claimed. Browser surfaces were unavailable, so HTTP/static checks are complete but visual dashboard review remains external.",
            "",
            "### GPU embedding batches",
            "",
            f"A separate model-ready profile encoded the same 128 development chunks, with maximum input length {batch['maximum_input_tokens']} tokens, at batch sizes 1/8/32/64. It used three randomized-order repeats, CUDA synchronization and vector-agreement checks. It did not batch generation or alter research settings. The first timing export is retained locally; the final export additionally verifies the input-length bound.",
            "",
            "| Batch | Median chunks/second | Peak allocated GPU bytes |",
            "| --- | ---: | ---: |",
            *[
                f"| {size} | {b[str(size)]['chunks_per_second']:.1f} | {b[str(size)]['peak_gpu_bytes']:,} |"
                for size in [1, 8, 32, 64]
            ],
            "",
            f"Batch 32 processes about {b['32']['chunks_per_second'] / b['1']['chunks_per_second']:.2f} times as many chunks per second as batch 1 on this workload, with higher allocated memory. Batch 64 is slower than 32 here and uses more memory. This illustrates a measured throughput/memory tradeoff rather than a rule that larger batches always improve speed. [Profile evidence](research_report/evidence/embedding_batch_profile.json) records all twelve measurements.",
            "",
            "The service has strict input schemas, one inference worker, a four-job bound, persisted statuses, explicit fallbacks, source provenance and local tracing. It is a loopback demonstration without authentication or a production reliability claim. Forty-six correctness tests, targeted type checks, wheel/container checks and both current GitHub CI workflows pass.",
        ]
    )
    report = block(report, "SERVICE_RESULTS", service_text)
    atomic_text(report_path, report)
    technical = Path("docs/TECHNICAL_FOUNDATIONS.md")
    text = technical.read_text().replace(
        "Final evaluation and artifact assembly are currently running.",
        "Final evaluation is complete; the progress report and released tables contain the measured results and their limits.",
    )
    text = block(
        text,
        "FINAL_INTERPRETATION",
        """## Connecting the completed results to the mathematics

The principal evidence-minus-magnitude differences are -0.0363 and -0.0095 F1, with intervals that cross zero. This does not prove that entity links are always useless. It says this extractor, scoring rule, sparsifier, shallow circuit, candidate pool and sample do not establish the proposed benefit. A weak feature, limited statistical precision and an optimization restriction can all matter; the current experiment does not independently identify their causal shares.

The prepared control removes the specific global-phase degeneracy, but its two evidence-guidance intervals still cross zero. An improvement in expressivity is a mathematical property; an improvement in answer F1 is an empirical property. They must be measured separately. The full report retains both controls rather than replacing one after seeing scores.

For a complete optimum, E(x*) <= E(x) for every feasible x under that coefficient array. This inequality contains no reference answer, supporting annotation or LLM likelihood. It therefore cannot imply that the generated answer is correct. The released error analysis demonstrates real cases of lower common energy and lower answer F1. It evaluates the relevance subset using the same full coefficients, avoiding the invalid comparison of energies from different graph weights.

A 1,200-token cap bounds formatted context but leaves room for different consumption and selected counts. Comparing it with a 500-question count result would additionally change the question population, since the token condition has 100 questions. Within-condition paired comparisons are interpretable; a raw cross-table difference does not isolate the effect of the cap. Larger candidate pools similarly change retrieval opportunities and optimization cost together.

The gate-cap diagnostic uses descending recorded floating-point fractions and an integer floor edge budget. Near a floating-point boundary, a value represented as 0.3999999999999999 can retain 17 of 45 edges rather than the 18 associated with an exact decimal 0.4. The artifact records the actual fraction, retained indices, trial costs and final circuit. The principal 0.5 fractions are exactly representable and unaffected. Final cap validation, not a rounded display label, establishes feasibility. Compiled gate cost is not monotonic in retained edges because routing and optimization can change.

The service measures an entire three-method comparison request, not a single generated token or one selector in isolation. Its p95 comes from only five repeated fictional requests. Batching measurements use synchronized GPU embedding operations on 128 fixed chunks; their scope differs from both the CPU service and dataset evaluation. An engineering number becomes useful when its workload, denominator, warm/cold state and resource conditions are explicit.

The 110 frozen optimization instances allow Qiskit/MILP experiments without loading an embedding model, raw dataset or generator. Reference solver optima in that bundle are analysis outputs, not answer annotations. The reproduction command passes only coefficients and constraints to the solver, then compares its output against the stored execution. Reconstructing saved statistical tables, rerunning a solver on fixed features, and rerunning end-to-end RAG are three different levels of reproduction.
""",
    )
    atomic_text(technical, text)
    sequence = Path("docs/DEVELOPMENT_SEQUENCE.md")
    text = block(
        sequence.read_text(),
        "COMPLETED_EVALUATION",
        """## Phase G completion — frozen outputs before interpretation

Finished all 18 primary configurations without changing their settings. Retained the one zero-feasible-shot failure and all failed cap diagnostics. Finished separate formulation, gate-cap and prepared-state controls. Audited 53,230 records across 24 grids, including independent tokenization/energy checks and recompilation of the gate-capped final circuits. All primary/formulation conditions use the same core source fingerprint; the prepared extension has a separate composite identity.

Generated full method tables, paired intervals, resource plots, token/corpus sensitivities and deterministic error examples. The principal sparsification comparison does not establish the intended evidence-guidance benefit. Kept the research framing comparative and diagnostic. No post-hoc noninferiority margin, winning-seed selection, physical-hardware claim or answer-based parameter adjustment was introduced.

Exported compressed public outcomes, common source snapshots and 110 frozen coefficient instances. Reconstructed all public tables without neural inference and reproduced four actual solver cases, matching selected IDs, full energies and line compilation. These checks complement the earlier exact restoration of all split/corpus files.

## Phase H completion checks — actual execution beyond fixtures

Ran real CPU-container ingestion and five repeated three-selector comparisons. Verified cache reuse, local traces, persistent corpus retrieval and exact job-response survival after recreating the container on the same state volume. The single untrusted-source input was not selected into context, so it supplies no generator-resistance evidence. Browser visual review remains unavailable and is not represented as completed.

Profiled GPU embedding batches on 128 fixed development chunks, with three randomized repeats and synchronized timing. Verified the 240-token bound and vector agreement. Preserved the initial local timing export and published the final length-validated measurement. These operational profiles did not change scientific settings. Final manuscript export, page inspection and the versioned artifact package follow these checks.
""",
    )
    atomic_text(sequence, text)
    print("Updated all three reports from completed audited evidence")


if __name__ == "__main__":
    main()
