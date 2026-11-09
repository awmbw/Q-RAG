# Research protocol

Version 1, frozen before new held-out model evaluation, November 10, 2026.

## Questions and scope

H1: Does a query-conditioned entity-link feature improve selection and generated answers under the same budget?
H2: At the same retained-edge budget, does evidence-guided sparsification preserve answer quality and full-objective quality better than coefficient-only, degree and random rules?
H3: How do compiled resources, feasibility and quality change under a fixed-count penalty versus a count-preserving QAOA mixer?

These are separate questions. A graph improvement is not a solver improvement. QAOA simulation is not hardware speedup. The narrower contribution is an encoding-aware, matched-budget study of evidence-guided sparsification. Novelty remains a bounded literature-search conclusion, not a guarantee that no related work exists.

## Data and controls

Use development examples for all parameter decisions. Preserve the earlier inspected HotpotQA material as development/historical evaluation. Prepare new held-out IDs from official development/validation partitions, excluding earlier evaluation IDs and normalized duplicate questions. MuSiQue uses its answerable subset, with train for development and official dev for held-out evaluation. Freeze IDs, order, source revisions and hashes before inference. No hidden-test claim is made.

Primary comparison: same candidates, input order, generator, prompt, decoding, graph features and feasibility constraints. Compare fixed count and token budget in separate experiments. Supply the full candidate text to the generator; use token-safe chunk representations for embedding. Record actual formatted token consumption. Oracle and empty-context results are diagnostics, never normal competitors.

## Outcomes and statistics

Primary task outcome: mean per-question answer token F1. Also report normalized exact match, supporting-document recall, complete annotated support, selected count, actual context/input tokens, time, memory, feasibility and failures. Use each dataset's official answer semantics; MuSiQue maximizes over aliases. Do not silently fix reference annotations.

Compare paired differences on the same questions. Bootstrap question IDs (10,000 resamples, seed 20261110), averaging solver repeats within question first. Show 95% percentile intervals and sample sizes. Predeclare principal comparisons, label the remaining comparisons exploratory, and apply Holm adjustment if reporting a family of significance tests. A confidence interval containing zero is not evidence of equality. No noninferiority claim is made without a predeclared tolerance and a suitable bound.

Primary sparsification comparison: evidence-guided versus absolute coefficient retention at half of available nonzero interaction edges, using the same full target objective and frozen graph weight. Secondary edge fractions: 0.25 and 0.75. Include full and gamma=0 controls. Compare MILP and QAOA on the identical quantum subset. Candidate truncation is relevance-based and independent of labels. Larger classical pool results are contextual results, not a direct quantum scaling comparison.

## Execution policy

Profile 50 development questions before selecting final run sizes. Target at least 500 held-out examples per dataset for classical generation, with a separately frozen smaller quantum subset. Record every attempted seed and failure. Quantum budget starts at p=1/2, three seeds, 64 parameter evaluations, 1,024 final shots; adjust only on development profiling and freeze actual settings before final runs. No seed is chosen because it wins on held-out data.

Record original and surrogate energies, actual constraint encoding, state preparation, mixer, auxiliary qubits, compiled two-qubit gates/depth, target connectivity and transpiler seed. Include infeasible shots and postselection costs. Ideal, shot-based and noisy simulations are distinct. No quantum hardware is currently allocated.

The laptop is the execution host; no paid services or purchases. Download public datasets/models from their primary hosts. Keep credentials and personal material local. Use checkpoints and avoid exhausting disk or system memory. Resource permission is not a reason to launch an uninformative experiment.

## Reporting and changes

Keep unfavorable results. Save failure records and use all attempted questions in primary answer denominators. Specify successful-only resource summaries. Freeze a main evaluation configuration before viewing outcomes; any later scientific change starts a declared new cycle. A method name containing "evidence" is a hypothesis, not proof of preservation.

Maintain a claim-to-artifact map in the final paper package. Submission, authorship approval, independent manual annotation and unavailable hardware remain explicit handoffs. No external messages or submissions are authorized by this protocol.

## Development decision recorded before final evaluation

Gamma=0.2 is selected by equal-weight mean development F1 over 100 questions per dataset. Evidence-guided half-edge versus absolute half-edge remains the principal sparsification comparison. Add a same-shot uniform feasible-sampling baseline because n=10,k=5 has only 252 feasible subsets. Report the study as an encoding-aware comparison; no noninferiority tolerance or quantum-superiority claim is adopted. Larger-candidate and corpus results are separately bounded settings.

## Secondary complete-gate-cap diagnostic

Before definitive held-out comparison analysis, add a separately labeled diagnostic on the first ten quantum IDs per dataset. Compare absolute and evidence-guided masks under a hard cap of 180 complete compiled line two-qubit gates, using three seeds and the same p=1/64-evaluation/1,024-shot settings. The cap is based on the approximately 177-gate development half-edge results. Search retention fractions from 1 to 0 in steps of 0.05, keep the largest tested feasible fraction, and verify the actual optimized circuit again. Record preprocessing cost and any cap violations/infeasible penalty control. This does not alter the 18-condition primary matrix or create a noninferiority claim.

The secondary formulation control also compares gamma=0 and gamma=0.2 under the same p=1 XY-QAOA settings, first 50 quantum IDs per dataset and three seeds. Its separate configurations are frozen before definitive comparative answer analysis. This tests scoring effects under QAOA as well as MILP; it does not replace the principal half-edge comparison.

## Development distribution diagnostic and preparation erratum

A separate numerical study uses the first 20 recorded MuSiQue development coefficient instances, relevance-reduced to 8/10/12/16 candidates with k=5. It trains p=1 XY and penalty circuits with the same 64-evaluation limit and three seeds. Exact statevector probabilities give optimum-hit probability, no-feasible probability and expected best feasible energy at 1/16/64/256/1,024 final draws. This uses no answer labels or additional LLM inference. Average repeats within question; sizes are nested and are not independent replications. Equal final draws do not equal equal total work because uniform feasible sampling has no angle training.

This diagnostic exposed an analytic limitation: with a feasible basis-state start, the first diagonal cost layer is a global phase. At p=1, gamma cannot affect probabilities, although optimizing the mixer angle against different objectives can still change the result. At p=2 only the later cost layer can produce relative phases. A regression check verifies the diagnosis.

Retain the original frozen matrix unchanged. Add the separately frozen [preparation control](../configs/preparation_control.json) on the same first 50 quantum IDs per dataset. Before cost evolution, apply one fixed pi/4 XY ring sweep to the seeded feasible basis state. This creates a nonuniform feasible superposition and is included in compilation. Compare base/full objectives, p=1/2 full circuits, half-edge absolute/evidence masks, MILP and same-draw random sampling. No preparation parameter is tuned on held-out answers. These post-freeze controls are exploratory and cannot retrospectively become confirmatory principal results. The extension's exact source and composite core/extension identity are archived separately.
