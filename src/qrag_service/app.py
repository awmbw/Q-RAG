"""Run: uvicorn qrag_service.app:app --host 127.0.0.1 --port 8000 --workers 1."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from qrag_service.jobs import Jobs, QueueFull
from qrag_service.schemas import CompareRequest, IngestRequest, QueryRequest


def configure_tracing():
    if os.getenv("QRAG_TRACE_CONSOLE") == "1":
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        provider = TracerProvider(
            resource=Resource.create({"service.name": "qrag-local"})
        )
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)


def create_app(engine=None, database: Path | None = None, capacity=4):
    @asynccontextmanager
    async def lifespan(application):
        configure_tracing()
        actual_engine = engine
        if actual_engine is None:
            from qrag_service.engine import Engine

            actual_engine = Engine(Path(os.getenv("QRAG_CACHE", ".cache/service")))
        application.state.jobs = Jobs(
            actual_engine,
            database or Path(os.getenv("QRAG_JOB_DB", ".cache/service/jobs.sqlite")),
            capacity,
        )
        try:
            yield
        finally:
            application.state.jobs.close()

    application = FastAPI(
        title="Q-RAG context comparison", version="0.2.0", lifespan=lifespan
    )

    @application.get("/")
    def dashboard():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @application.get("/health")
    def health():
        return {
            "status": "ok",
            "worker_policy": "one inference worker; bounded queue",
            "quantum_hardware": False,
        }

    @application.get("/ready")
    def ready():
        initialized = application.state.jobs.engine.ready
        return JSONResponse(
            {
                "ready": initialized,
                "state": "model_ready"
                if initialized
                else "cold; first job loads local models",
            },
            status_code=200 if initialized else 503,
        )

    @application.post("/jobs", status_code=202)
    def submit(request: CompareRequest):
        try:
            job_id = application.state.jobs.submit(request)
        except QueueFull as exc:
            raise HTTPException(429, str(exc), headers={"Retry-After": "5"}) from exc
        return {"id": job_id, "status_url": "/jobs/" + job_id}

    @application.get("/jobs/{job_id}")
    def job(job_id: str):
        result = application.state.jobs.get(job_id)
        if result is None:
            raise HTTPException(404, "Job not found")
        return result

    def enqueue(request):
        try:
            job_id = application.state.jobs.submit(request)
        except QueueFull as exc:
            raise HTTPException(429, str(exc), headers={"Retry-After": "5"}) from exc
        return {"id": job_id, "status_url": "/jobs/" + job_id}

    @application.post("/corpora", status_code=202)
    def ingest(request: IngestRequest):
        return enqueue(request)

    @application.post("/query", status_code=202)
    def query(request: QueryRequest):
        return enqueue(request)

    @application.get("/metrics")
    def metrics():
        return application.state.jobs.metrics()

    return application


app = create_app()
