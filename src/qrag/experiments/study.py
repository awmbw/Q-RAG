"""Configuration-driven study on shared, token-safe candidate representations."""

import argparse
import json
import traceback
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

import numpy as np

from qrag.config import ExperimentConfig
from qrag.data import load_examples
from qrag.datasets import score_answer, score_evidence
from qrag.evidence import cached_evidence, interaction_problem
from qrag.experiments.artifacts import (
    environment,
    file_hash,
    source_hash,
    utc_now,
    write_json,
)
from qrag.experiments.journal import JournalRunStore
from qrag.models import LocalModels
from qrag.optimization import (
    select_annealing,
    select_greedy,
    select_milp,
    select_random_samples,
    select_top_k,
)
from qrag.retrieval import (
    ChunkEncoder,
    ChunkReranker,
    bm25_scores,
    reciprocal_rank_fusion,
)


def summarize(records):
    result = {"methods": {}}
    for method in sorted({r["method"] for r in records}):
        rows = [r for r in records if r["method"] == method]
        good = [r for r in rows if r["status"] == "success"]
        metrics = {
            key: sum(r.get("metrics", {}).get(key, 0.0) for r in rows) / len(rows)
            for key in ("answer_f1", "answer_em")
        }
        means = {}
        for key in ("document_recall", "all_supporting_documents"):
            values = [r["metrics"][key] for r in good if r["metrics"][key] is not None]
            means[key + "_successful_only"] = float(np.mean(values)) if values else None
        for key in (
            "context_tokens",
            "input_tokens",
            "selected_count",
            "selection_seconds",
            "generation_seconds",
        ):
            means[key + "_successful_only"] = (
                float(np.mean([r[key] for r in good])) if good else None
            )
        result["methods"][method] = {
            "questions": len(rows),
            "failures": len(rows) - len(good),
            **metrics,
            **means,
        }
    return result


def validate_spec(spec):
    allowed = {
        "model",
        "methods",
        "budget_mode",
        "context_budget",
        "candidate_limit",
        "reranker",
        "scope",
        "cache",
        "seed",
        "limit",
        "dataset_sha256",
    }
    if set(spec) - allowed:
        raise ValueError(f"Unknown study settings: {set(spec) - allowed}")
    config = ExperimentConfig(**spec["model"])
    methods = spec["methods"]
    if not methods or len({m["name"] for m in methods}) != len(methods):
        raise ValueError("Method names must be nonempty and unique")
    for m in methods:
        if m["solver"] not in {
            "top_k",
            "bm25",
            "hybrid",
            "reranker",
            "mmr",
            "coverage",
            "greedy",
            "annealing",
            "milp",
            "qaoa",
            "random",
        }:
            raise ValueError("Unknown solver")
    if spec.get("budget_mode", "count") not in {"count", "tokens"}:
        raise ValueError("Unknown budget mode")
    if spec.get("budget_mode") == "tokens" and (
        type(spec.get("context_budget")) is not int or spec["context_budget"] < 1
    ):
        raise ValueError("Need positive context token budget")
    if (
        type(spec.get("candidate_limit", 100)) is not int
        or spec.get("candidate_limit", 100) < 1
    ):
        raise ValueError("Invalid candidate limit")
    return config


def choose(problem, method, relevance, similarities, coverage, lexical, rerank):
    solver = method["solver"]
    if solver in {"top_k", "bm25", "hybrid", "reranker"}:
        scores = {
            "top_k": relevance,
            "bm25": lexical,
            "hybrid": reciprocal_rank_fusion(relevance, lexical),
            "reranker": rerank,
        }[solver]
        if scores is None:
            raise ValueError("Reranker not configured")
        return select_top_k(problem, scores), {}
    if solver in {"mmr", "coverage", "greedy"}:
        return select_greedy(
            problem,
            relevance,
            similarities,
            coverage,
            {"greedy": "energy"}.get(solver, solver),
        ), {}
    if solver == "annealing":
        return select_annealing(
            problem, method.get("seed", 42), method.get("steps", 2000)
        ), {}
    if solver == "milp":
        return select_milp(problem, method.get("time_limit", 10)), {}
    if solver == "random":
        return select_random_samples(
            problem, method.get("seed", 42), method.get("shots", 1024)
        )
    from qrag.quantum import solve_qaoa

    return solve_qaoa(
        problem,
        **{
            k: v
            for k, v in method.items()
            if k
            in {"p", "seed", "shots", "max_evals", "mixer", "noise", "training_shots"}
        },
    )


def run_study(spec, output: Path, resume=False, backend=None):
    config = validate_spec(spec)
    path = Path(config.dataset)
    if spec.get("dataset_sha256") and file_hash(path) != spec["dataset_sha256"]:
        raise ValueError("Dataset hash mismatch")
    examples = load_examples(path)[: config.limit]
    model = backend if backend is not None else LocalModels(config)
    identity = {
        "spec": spec,
        "data_sha256": file_hash(path),
        "source_sha256": source_hash(),
        "question_ids": [q.id for q, _ in examples],
        "environment": environment(),
        "backend": {
            "device": model.device,
            "dtype": config.generator_dtype,
            "embedding_model": config.embedding_model,
            "embedding_revision": config.embedding_revision,
            "generator_model": config.generator_model,
            "generator_revision": config.generator_revision,
        },
    }
    store = JournalRunStore(output, identity, resume)
    expected = {(q.id, m["name"]) for q, _ in examples for m in spec["methods"]}
    if not set(store.records) <= expected:
        raise ValueError("Unexpected records")
    if set(store.records) == expected and all(
        r["status"] == "success" for r in store.records.values()
    ):
        result = summarize(list(store.records.values()))
        write_json(output / "summary.json", result)
        return result
    # Retain exact source bytes even when implementation changes in later phases.
    root = Path(__file__).resolve().parents[1]
    if not (output / "source_snapshot.json").exists():
        write_json(
            output / "source_snapshot.json",
            {
                str(p.relative_to(root)): p.read_text()
                for p in sorted(root.rglob("*.py"))
            },
        )
    invocation = {"started_at": utc_now()}
    start = perf_counter()
    store.manifest["invocations"].append(invocation)
    store.manifest["status"] = "running"
    store.save_manifest()
    encoder = None
    try:
        invocation["preparation"] = model.prepare()
        encoder = ChunkEncoder(
            model.embedder,
            Path(spec.get("cache", ".cache/study_embeddings.sqlite")),
            config.embedding_model,
            config.embedding_revision,
        )
        reranker = None
        if any(m["solver"] == "reranker" for m in spec["methods"]):
            r = spec["reranker"]
            reranker = ChunkReranker(r["model"], r["revision"], encoder, model.device)
        store.save_manifest()
        for query, labels in examples:
            pending = [
                m
                for m in spec["methods"]
                if (query.id, m["name"]) not in store.records
                or store.records[(query.id, m["name"])]["status"] != "success"
            ]
            if not pending:
                continue
            shared_error = None
            try:
                if (
                    len(query.documents) < config.k
                    and config.short_pool_policy == "error"
                    and spec.get("budget_mode", "count") == "count"
                ):
                    raise ValueError("Candidate pool smaller than requested k")
                relevance, similarities, features = encoder.score(query)
                candidate_limit = spec.get("candidate_limit", 100)
                if len(query.documents) > candidate_limit:
                    order = sorted(
                        int(i)
                        for i in np.argsort(-relevance, kind="stable")[:candidate_limit]
                    )
                    query = replace(
                        query, documents=tuple(query.documents[i] for i in order)
                    )
                    relevance = relevance[order]
                    similarities = similarities[np.ix_(order, order)]
                comp, coverage, graph = cached_evidence(
                    query, relevance, Path(".cache/study_graphs.sqlite")
                )
                feature_started = perf_counter()
                lexical = bm25_scores(query.question, query.documents)
                features["lexical_seconds"] = perf_counter() - feature_started
                feature_started = perf_counter()
                rerank = reranker.score(query) if reranker else None
                features["rerank_seconds"] = (
                    perf_counter() - feature_started if reranker else None
                )
                features["graph_lookup_seconds"] = graph["lookup_seconds"]
                mode = spec.get("budget_mode", "count")
                budgets = {}
                if mode == "tokens":
                    # Conservative additive accounting, then exact formatted verification.
                    costs = np.array(
                        [
                            len(
                                model.tokenizer.encode(
                                    f"[Source {d.id}: {d.title}]\n{d.text}",
                                    add_special_tokens=False,
                                )
                            )
                            + 10
                            for d in query.documents
                        ]
                    )
                    budgets = {
                        "token_costs": costs,
                        "token_budget": spec["context_budget"],
                        "min_count": 1,
                    }
                k = min(config.k, len(query.documents)) if mode == "count" else None
            except Exception as exc:
                shared_error = exc
            generations = {}
            for method in pending:
                row = {
                    "question_id": query.id,
                    "method": method["name"],
                    "status": "error",
                    "candidate_ids": [d.id for d in query.documents],
                }
                row["candidate_metrics"] = score_evidence(query.documents, labels)
                try:
                    if shared_error:
                        raise shared_error
                    full = interaction_problem(
                        relevance,
                        similarities,
                        k,
                        method.get("gamma", 0),
                        comp,
                        config.alpha,
                        config.beta,
                        **budgets,
                    )
                    problem = full
                    sparse_meta = {}
                    if method.get("sparsifier"):
                        from qrag.sparsification import sparsify

                        problem, sparse_meta = sparsify(
                            full,
                            comp,
                            method["sparsifier"],
                            method.get("edge_fraction", 0.5),
                            method.get("seed", 42),
                        )
                    selection, resources = choose(
                        problem,
                        method,
                        relevance,
                        similarities,
                        coverage,
                        lexical,
                        rerank,
                    )
                    row.update(
                        {
                            "selection": asdict(selection),
                            "resources": resources,
                            "sparsification": sparse_meta,
                            "linear_coefficients": full.linear.tolist(),
                            "pair_coefficients": full.pairs.tolist(),
                            "surrogate_pairs": problem.pairs.tolist(),
                            "features": features,
                            "graph": graph,
                        }
                    )
                    if selection.indices is None:
                        raise RuntimeError(
                            "Solver returned no feasible solution: " + selection.status
                        )
                    full.validate_selection(selection.indices)
                    selected = tuple(query.documents[i] for i in selection.indices)
                    reused = selection.indices in generations
                    generation = generations.get(selection.indices)
                    if generation is None:
                        generation = model.generate(query, selected)
                        generations[selection.indices] = generation
                    if (
                        mode == "tokens"
                        and generation["context_tokens"] > spec["context_budget"]
                    ):
                        raise ValueError(
                            "Actual assembled context exceeds token budget; no silent repair"
                        )
                    row.update(generation)
                    row.update(
                        {
                            "generation_reused": reused,
                            "actual_generation_seconds": 0.0
                            if reused
                            else generation["generation_seconds"],
                            "selected_ids": [d.id for d in selected],
                            "selected_titles": [d.title for d in selected],
                            "selected_count": len(selected),
                            "selection_seconds": selection.seconds,
                            "full_energy": full.energy(selection.indices),
                            "surrogate_energy": problem.energy(selection.indices),
                            "feasible": True,
                            "budget_mode": mode,
                            "estimated_token_cost": float(
                                sum(costs[list(selection.indices)])
                            )
                            if mode == "tokens"
                            else None,
                            "metrics": {
                                **score_answer(generation["answer"], labels),
                                **score_evidence(selected, labels),
                            },
                            "status": "success",
                        }
                    )
                except Exception as exc:
                    row.update({"error_type": type(exc).__name__, "error": str(exc)})
                store.save_record(row)
                print(query.id, method["name"], row["status"], flush=True)
        result = summarize(list(store.records.values()))
        write_json(output / "summary.json", result)
        store.manifest["status"] = (
            "completed_with_errors"
            if any(r["status"] != "success" for r in store.records.values())
            else "completed"
        )
        return result
    except BaseException:
        store.manifest["status"] = "interrupted_or_failed"
        write_json(output / "failure.json", {"traceback": traceback.format_exc()})
        raise
    finally:
        invocation.update(
            {"ended_at": utc_now(), "wall_seconds": perf_counter() - start}
        )
        store.save_manifest()
        if encoder:
            encoder.cache.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    result = run_study(json.loads(args.config.read_text()), args.output, args.resume)
    print(json.dumps(result, indent=2))
    if any(m["failures"] for m in result["methods"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
