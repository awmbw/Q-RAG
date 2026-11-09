"""Run fixed-count top-k and MILP on shared candidates, then score actual answers."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
from time import perf_counter
import traceback

import numpy as np

from qrag.config import ExperimentConfig, load_config
from qrag.data import load_examples
from qrag.experiments.artifacts import (
    RunStore, environment, file_hash, source_hash, utc_now, write_json,
)
from qrag.metrics import answer_metrics, evidence_metrics
from qrag.optimization import build_problem, select_milp, select_top_k

METHODS = ("top_k", "milp")


def summarize(records: list[dict]) -> dict:
    summary = {"scope": "development_smoke_run", "methods": {}}
    for method in METHODS:
        rows = [record for record in records if record["method"] == method]
        good = [record for record in rows if record["status"] == "success"]
        count = len(rows)
        means = {}
        for metric in ("answer_em", "answer_f1"):
            means[f"{metric}_all_questions"] = (
                sum(record.get("metrics", {}).get(metric, 0.0) for record in rows) / count
                if count else None
            )
        for metric in ("document_recall", "all_supporting_documents"):
            observed = [record["metrics"][metric] for record in good
                        if record["metrics"][metric] is not None]
            means[f"{metric}_successful_only"] = float(np.mean(observed)) if observed else None
        for key in ("selected_count", "context_tokens", "input_tokens", "generation_seconds"):
            means[f"mean_{key}_successful_only"] = (
                float(np.mean([record[key] for record in good])) if good else None
            )
        summary["methods"][method] = {
            "questions": count, "successful": len(good), "failed": count - len(good),
            **means,
        }
    return summary


def run_experiment(
    config: ExperimentConfig, output: Path, *, resume: bool = False, backend=None,
) -> dict:
    """Backend injection is for offline tests; the CLI always uses real local models."""
    random.seed(config.seed)
    np.random.seed(config.seed)
    dataset_path = Path(config.dataset).resolve()
    examples = load_examples(dataset_path)[:config.limit]
    if backend is None:
        from qrag.models import LocalModels
        backend = LocalModels(config)
    identity = {
        "config": config.as_dict(), "dataset_sha256": file_hash(dataset_path),
        "question_ids": [query.id for query, _ in examples],
        "source_sha256": source_hash(), "environment": environment(),
        "backend": backend.describe(), "methods": METHODS,
        "context_order": "original_candidate_order",
        "budget_mode": "exact_count",
        "cache_policy": "shared_features_per_question_only; no_persistent_embedding_cache",
    }
    store = RunStore(output, identity, resume)
    expected_keys = {(query.id, method) for query, _ in examples for method in METHODS}
    if not set(store.records) <= expected_keys:
        raise ValueError("Stored records contain unexpected questions or methods")
    if set(store.records) == expected_keys:
        result = summarize(list(store.records.values()))
        write_json(output / "summary.json", result)
        return result
    invocation = {"started_at": utc_now()}
    start = perf_counter()
    store.manifest["invocations"].append(invocation)
    store.manifest["status"] = "running"
    store.save_manifest()
    try:
        invocation["preparation"] = backend.prepare()
        store.save_manifest()
        for query, labels in examples:
            pending = [method for method in METHODS if (query.id, method) not in store.records]
            if not pending:
                continue
            feature_error = None
            features = {}
            effective_k = min(config.k, len(query.documents))
            try:
                if config.k > len(query.documents) and config.short_pool_policy == "error":
                    raise ValueError("Candidate pool is smaller than requested k")
                relevance, similarities, features = backend.score(query)
                problem = build_problem(relevance, similarities, effective_k,
                                        config.alpha, config.beta)
            except Exception as exc:
                feature_error = exc
            for method in pending:
                record = {
                    "question_id": query.id, "method": method,
                    "requested_k": config.k, "effective_k": effective_k,
                    "candidate_ids": [doc.id for doc in query.documents],
                    "features": features,
                }
                try:
                    if feature_error is not None:
                        raise feature_error
                    selection = (select_top_k(problem, relevance) if method == "top_k"
                                 else select_milp(problem, config.solver_time_limit))
                    record["selection"] = asdict(selection)
                    if selection.indices is None:
                        raise RuntimeError(f"No feasible incumbent: {selection.status}")
                    problem.validate_selection(selection.indices)
                    selected = tuple(query.documents[i] for i in selection.indices)
                    record.update({
                        "selected_ids": [doc.id for doc in selected],
                        "selected_titles": [doc.title for doc in selected],
                        "selected_count": len(selected), "feasible": True,
                        "relevance_scores": relevance.tolist(),
                        "linear_coefficients": problem.linear.tolist(),
                        "pair_coefficients": problem.pairs.tolist(),
                    })
                    # No labels enter either score(), selection, or generate().
                    generation = backend.generate(query, selected)
                    record.update(generation)
                    record["metrics"] = {
                        **answer_metrics(generation["answer"], labels.answer),
                        **evidence_metrics(selected, labels),
                    }
                    record["status"] = "success"
                except Exception as exc:
                    record.update({"status": "error", "error_type": type(exc).__name__,
                                   "error": str(exc)})
                store.save_record(record)
                print(f"{query.id} {method}: {record['status']}", flush=True)
        result = summarize(list(store.records.values()))
        write_json(output / "summary.json", result)
        store.manifest["status"] = "completed_with_errors" if any(
            row["status"] != "success" for row in store.records.values()
        ) else "completed"
        return result
    except BaseException:
        store.manifest["status"] = "interrupted_or_failed"
        write_json(output / "failure.json", {"traceback": traceback.format_exc()})
        raise
    finally:
        invocation.update({"ended_at": utc_now(), "wall_seconds": perf_counter() - start})
        store.save_manifest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        summary = run_experiment(load_config(args.config), args.output, resume=args.resume)
    except Exception as exc:
        parser.exit(1, f"Experiment failed: {exc}\n")
    print(json.dumps(summary, indent=2))
    if any(value["failed"] for value in summary["methods"].values()):
        parser.exit(1, "Run completed with recorded errors; inspect predictions.jsonl.\n")


if __name__ == "__main__":
    main()
