"""Freeze the final evaluation configurations before observing their outcomes."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from qrag.config import ExperimentConfig
from qrag.experiments.artifacts import file_hash, write_json


def main():
    path = Path("configs/final_matrix.json")
    if path.exists():
        raise FileExistsError("Final matrix already frozen")
    revisions = json.loads(Path("configs/model_revisions.json").read_text())
    split = json.loads(Path("configs/splits/research_v1.json").read_text())
    corpus = json.loads(Path("configs/splits/corpus_v1.json").read_text())
    gamma = json.loads(Path("configs/development_decision.json").read_text())["gamma"]
    classical = [
        {"name": s, "solver": s}
        for s in ["top_k", "bm25", "hybrid", "reranker", "mmr", "coverage", "greedy"]
    ]
    classical += [
        {"name": "milp_base", "solver": "milp"},
        {"name": "milp_full", "solver": "milp", "gamma": gamma},
    ]
    for solver in ["annealing", "random"]:
        for seed in [41, 42, 43]:
            classical.append(
                {
                    "name": f"{solver}_full_s{seed}",
                    "solver": solver,
                    "seed": seed,
                    "gamma": gamma,
                    "shots": 1024,
                }
            )
    for rule in ["absolute", "evidence"]:
        for fraction in [0.5, 0.75]:
            classical.append(
                {
                    "name": f"milp_{rule}_f{fraction}",
                    "solver": "milp",
                    "gamma": gamma,
                    "sparsifier": rule,
                    "edge_fraction": fraction,
                }
            )
    quantum = [
        {"name": "milp_base", "solver": "milp"},
        {"name": "milp_full", "solver": "milp", "gamma": gamma},
    ]
    for seed in [41, 42, 43]:
        quantum.append(
            {
                "name": f"random_full_s{seed}",
                "solver": "random",
                "gamma": gamma,
                "seed": seed,
                "shots": 1024,
            }
        )
        for depth in [1, 2]:
            quantum.append(
                {
                    "name": f"xy_full_p{depth}_s{seed}",
                    "solver": "qaoa",
                    "gamma": gamma,
                    "p": depth,
                    "mixer": "xy",
                    "seed": seed,
                    "shots": 1024,
                    "max_evals": 64,
                }
            )
        for rule in ["absolute", "random", "degree", "evidence"]:
            quantum.append(
                {
                    "name": f"xy_{rule}_f0.5_s{seed}",
                    "solver": "qaoa",
                    "gamma": gamma,
                    "p": 1,
                    "mixer": "xy",
                    "seed": seed,
                    "shots": 1024,
                    "max_evals": 64,
                    "sparsifier": rule,
                    "edge_fraction": 0.5,
                }
            )
        for rule in ["full", "absolute", "evidence"]:
            method = {
                "name": f"penalty_{rule}_s{seed}",
                "solver": "qaoa",
                "gamma": gamma,
                "p": 1,
                "mixer": "penalty",
                "seed": seed,
                "shots": 1024,
                "max_evals": 64,
            }
            if rule != "full":
                method.update({"sparsifier": rule, "edge_fraction": 0.5})
            quantum.append(method)
    matrix = []

    def save(name, spec, role):
        config = Path("configs/final") / (name + ".json")
        write_json(config, spec)
        matrix.append(
            {"config": str(config), "sha256": file_hash(config), "role": role}
        )

    for dataset in ["hotpotqa", "musique"]:
        metadata = split["datasets"][dataset]["splits"]["evaluation"]
        for generator, tag, revision in [
            (
                "Qwen/Qwen2.5-1.5B-Instruct",
                "qwen15",
                ExperimentConfig().generator_revision,
            ),
            (
                "Qwen/Qwen2.5-3B-Instruct",
                "qwen3",
                revisions["Qwen/Qwen2.5-3B-Instruct"],
            ),
        ]:
            model = replace(
                ExperimentConfig(),
                dataset=metadata["path"],
                limit=500,
                device="cuda",
                generator_dtype="float16",
                generator_model=generator,
                generator_revision=revision,
            ).as_dict()
            spec = {
                "model": model,
                "dataset_sha256": metadata["sha256"],
                "scope": "frozen held-out supplied-pool count evaluation",
                "budget_mode": "count",
                "methods": deepcopy(classical),
                "reranker": {
                    "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
                    "revision": revisions["cross-encoder/ms-marco-MiniLM-L6-v2"],
                },
            }
            save(
                f"final_{dataset}_{tag}_count",
                spec,
                "primary classical answer evaluation; 500 questions",
            )
            tokens = deepcopy(spec)
            tokens["model"]["limit"] = 100
            tokens["budget_mode"] = "tokens"
            tokens["context_budget"] = 1200
            tokens["scope"] = (
                "frozen held-out token-budget evaluation; separate from count study"
            )
            tokens["methods"] = [
                m for m in tokens["methods"] if m["solver"] != "random"
            ]
            save(
                f"final_{dataset}_{tag}_tokens",
                tokens,
                "secondary token-budget study; first 100 frozen IDs",
            )
        model = replace(
            ExperimentConfig(),
            dataset=metadata["path"],
            limit=50,
            device="cuda",
            generator_dtype="float16",
        ).as_dict()
        spec = {
            "model": model,
            "dataset_sha256": metadata["sha256"],
            "scope": "frozen held-out quantum study; first 50 IDs, label-independent top-10 relevance reduction",
            "budget_mode": "count",
            "candidate_limit": 10,
            "methods": deepcopy(quantum),
        }
        save(
            f"final_{dataset}_quantum",
            spec,
            "primary quantum comparison; same reduced pool for all methods",
        )
        for size, count in [(25, 100), (50, 30), (100, 30)]:
            cm = corpus["datasets"][dataset]["candidate_files"][str(size)]
            model = replace(
                ExperimentConfig(),
                dataset=cm["path"],
                limit=count,
                device="cuda",
                generator_dtype="float16",
            ).as_dict()
            methods = [
                deepcopy(m)
                for m in classical
                if m["name"]
                in [
                    "top_k",
                    "bm25",
                    "hybrid",
                    "reranker",
                    "coverage",
                    "greedy",
                    "milp_base",
                    "milp_full",
                ]
            ]
            for m in methods:
                if m["solver"] == "milp":
                    m["time_limit"] = 1.0
            save(
                f"final_{dataset}_corpus{size}",
                {
                    "model": model,
                    "dataset_sha256": cm["sha256"],
                    "scope": "bounded-corpus retrieval; supplied-pool results are separate",
                    "budget_mode": "count",
                    "methods": methods,
                    "reranker": deepcopy(
                        spec.get(
                            "reranker",
                            {
                                "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
                                "revision": revisions[
                                    "cross-encoder/ms-marco-MiniLM-L6-v2"
                                ],
                            },
                        )
                    ),
                },
                f"bounded corpus, {size} candidates; MILP 1-second limit, {count} questions",
            )
    # Larger quantum pools come from MuSiQue's actual ~20 supplied paragraphs.
    metadata = split["datasets"]["musique"]["splits"]["evaluation"]
    for size in [12, 16]:
        methods = [
            m
            for m in quantum
            if m["name"] == "milp_full"
            or m["name"].startswith("random_full")
            or m["name"].startswith("xy_full_p1")
            or m["name"].startswith("xy_absolute")
            or m["name"].startswith("xy_evidence")
        ]
        save(
            f"final_musique_quantum{size}",
            {
                "model": replace(
                    ExperimentConfig(),
                    dataset=metadata["path"],
                    limit=5,
                    device="cuda",
                    generator_dtype="float16",
                ).as_dict(),
                "dataset_sha256": metadata["sha256"],
                "scope": "bounded larger-quantum sensitivity; first five frozen IDs; no fabricated candidates",
                "budget_mode": "count",
                "candidate_limit": size,
                "methods": deepcopy(methods),
            },
            "small scaling sensitivity, not a powered answer-quality study",
        )
    write_json(
        path,
        {
            "frozen_before_held_out_execution": True,
            "gamma": gamma,
            "principal_comparison": "xy_evidence_f0.5 versus xy_absolute_f0.5 on same 50 questions per dataset; three seeds averaged within question",
            "primary_generators": "Qwen 1.5B and 3B on full classical supplied pools; primary quantum uses 1.5B",
            "configs": matrix,
            "notes": "No noninferiority tolerance adopted. Negative findings retained. Larger quantum/corpus and token studies have separate sample counts.",
        },
    )
    print("Frozen", len(matrix), "configurations")


if __name__ == "__main__":
    main()
