"""Serialized local inference; no labels, external API calls or silent fallback."""

import os
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import numpy as np
from opentelemetry import trace

from qrag.config import ExperimentConfig
from qrag.corpus import CorpusRetriever
from qrag.data import Document, QueryInput
from qrag.evidence import cached_evidence, interaction_problem
from qrag.experiments.artifacts import value_hash
from qrag.models import LocalModels
from qrag.optimization import select_greedy, select_milp, select_top_k
from qrag.quantum import solve_qaoa
from qrag.retrieval import ChunkEncoder
from qrag_service.schemas import CompareRequest, IngestRequest, QueryRequest

TRACER = trace.get_tracer("qrag.service")


class Engine:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.ready = False
        self.model = None
        self.encoder = None
        self.preparation = None
        self.corpora = {}

    def warmup(self):
        if self.ready:
            return
        import torch

        device = os.getenv("QRAG_DEVICE", "auto")
        gpu = torch.cuda.is_available() and device != "cpu"
        config = replace(
            ExperimentConfig(),
            device=device,
            generator_dtype="float16" if gpu else "float32",
            embedding_model=os.getenv(
                "QRAG_EMBEDDING_MODEL", ExperimentConfig().embedding_model
            ),
            embedding_revision=os.getenv(
                "QRAG_EMBEDDING_REVISION", ExperimentConfig().embedding_revision
            ),
            generator_model=os.getenv(
                "QRAG_GENERATOR_MODEL", ExperimentConfig().generator_model
            ),
            generator_revision=os.getenv(
                "QRAG_GENERATOR_REVISION", ExperimentConfig().generator_revision
            ),
        )
        with TRACER.start_as_current_span("model.prepare"):
            self.model = LocalModels(config)
            self.preparation = self.model.prepare()
            self.encoder = ChunkEncoder(
                self.model.embedder,
                self.cache_dir / "embeddings.sqlite",
                config.embedding_model,
                config.embedding_revision,
            )
        self.ready = True

    def execute(self, request, job_id):
        started = perf_counter()
        self.warmup()
        timings = {}
        retrieval = None
        if isinstance(request, IngestRequest):
            with TRACER.start_as_current_span("corpus.ingest"):
                corpus = CorpusRetriever.build(
                    self.cache_dir / "corpora" / request.corpus,
                    [Document(s.id, s.title, s.text) for s in request.sources],
                    self.encoder,
                )
                self.corpora[request.corpus] = corpus
            return {
                "job_id": job_id,
                "corpus": request.corpus,
                "manifest": corpus.manifest,
                "wall_seconds": perf_counter() - started,
            }
        if isinstance(request, QueryRequest):
            with TRACER.start_as_current_span("corpus.retrieve"):
                if request.corpus not in self.corpora:
                    self.corpora[request.corpus] = CorpusRetriever(
                        self.cache_dir / "corpora" / request.corpus, self.encoder
                    )
                sources, retrieval = self.corpora[request.corpus].retrieve(
                    request.question, request.candidates, request.retrieval
                )
            request = CompareRequest(
                question=request.question,
                sources=[
                    {"id": d.id, "title": d.title, "text": d.text} for d in sources
                ],
                methods=request.methods,
                k=request.k,
                allow_classical_fallback=request.allow_classical_fallback,
                deadline_seconds=request.deadline_seconds,
            )

        def check_deadline():
            if perf_counter() - started > request.deadline_seconds:
                raise TimeoutError("Job deadline exceeded between bounded stages")

        query = QueryInput(
            "request:"
            + value_hash(
                {
                    "question": request.question,
                    "sources": [(s.id, s.title, s.text) for s in request.sources],
                }
            ),
            request.question,
            tuple(Document(s.id, s.title, s.text) for s in request.sources),
        )
        with TRACER.start_as_current_span(
            "rag.compare",
            attributes={"job.id": job_id, "sources.count": len(query.documents)},
        ):
            check_deadline()
            stage = perf_counter()
            with TRACER.start_as_current_span("embedding.score"):
                relevance, similarities, features = self.encoder.score(query)
            timings["embedding_seconds"] = perf_counter() - stage
            original_count = len(query.documents)
            if "qaoa" in request.methods and original_count > 10:
                order = sorted(
                    int(i) for i in np.argsort(-relevance, kind="stable")[:10]
                )
                query = replace(
                    query, documents=tuple(query.documents[i] for i in order)
                )
                relevance = relevance[order]
                similarities = similarities[np.ix_(order, order)]
            check_deadline()
            stage = perf_counter()
            with TRACER.start_as_current_span("evidence.graph"):
                comp, coverage, graph = cached_evidence(
                    query, relevance, self.cache_dir / "graphs.sqlite"
                )
            timings["graph_seconds"] = perf_counter() - stage
            problem = interaction_problem(relevance, similarities, request.k, 0.2, comp)
            results = []
            generations = {}
            for method in request.methods:
                check_deadline()
                fallback = None
                resources = {}
                with TRACER.start_as_current_span("selection." + method):
                    if method == "relevance":
                        selection = select_top_k(problem, relevance)
                    elif method == "mmr":
                        selection = select_greedy(
                            problem, relevance, similarities, coverage, "mmr"
                        )
                    elif method == "milp":
                        selection = select_milp(
                            problem, min(10.0, request.deadline_seconds)
                        )
                    else:
                        try:
                            selection, resources = solve_qaoa(
                                problem,
                                p=1,
                                shots=1024,
                                max_evals=64,
                                seed=42,
                                mixer="xy",
                            )
                            if selection.indices is None:
                                raise RuntimeError("No feasible quantum sample")
                        except Exception as exc:
                            if not request.allow_classical_fallback:
                                raise
                            fallback = {
                                "used": True,
                                "method": "milp",
                                "reason": type(exc).__name__ + ": " + str(exc)[:200],
                            }
                            selection = select_milp(
                                problem, min(10.0, request.deadline_seconds)
                            )
                check_deadline()
                if selection.indices is None:
                    raise RuntimeError("No feasible selected context")
                selected = tuple(query.documents[i] for i in selection.indices)
                reused = selection.indices in generations
                with TRACER.start_as_current_span("generation." + method):
                    if not reused:
                        generations[selection.indices] = self.model.generate(
                            query, selected
                        )
                    generation = generations[selection.indices]
                check_deadline()
                results.append(
                    {
                        "requested_method": method,
                        "actual_method": "milp" if fallback else method,
                        "fallback": fallback,
                        "answer": generation["answer"],
                        "supplied_sources": [
                            {"id": d.id, "title": d.title} for d in selected
                        ],
                        "context_tokens": generation["context_tokens"],
                        "input_tokens": generation["input_tokens"],
                        "selection_seconds": selection.seconds,
                        "generation_seconds": generation["generation_seconds"],
                        "generation_reused": reused,
                        "full_energy": problem.energy(selection.indices),
                        "solver_status": selection.status,
                        "optimal": selection.optimal,
                        "quantum_resources": resources or None,
                    }
                )
        return {
            "job_id": job_id,
            "results": results,
            "candidate_count": len(query.documents),
            "candidate_sources": [
                {"id": d.id, "title": d.title, "text": d.text} for d in query.documents
            ],
            "retrieval": retrieval,
            "original_source_count": original_count,
            "candidate_policy": "common top-10 relevance pool for all methods when QAOA is requested"
            if original_count > len(query.documents)
            else "all supplied sources",
            "backend": {
                "device": self.model.device,
                "generator": self.model.config.generator_model,
                "revision": self.model.config.generator_revision,
                "dtype": self.model.config.generator_dtype,
            },
            "graph": graph,
            "features": features,
            "stage_timings": timings,
            "wall_seconds": perf_counter() - started,
            "source_note": "Supplied sources identify context given to the model; they do not prove the answer used each source.",
            "quantum_note": "QAOA runs in classical simulation. Any classical fallback is labeled separately.",
        }

    def close(self):
        if self.encoder is not None:
            self.encoder.cache.close()
