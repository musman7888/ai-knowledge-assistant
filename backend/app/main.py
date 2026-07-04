# ============================================================
# FASTAPI ENTRY POINT
# Creates the web application and defines the first two endpoints.
# Run locally:  uvicorn app.main:app --reload
# ============================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api import ask, upload
from app.services import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once on startup: seed the sample document if the store is empty."""
    rag_service.seed_sample_if_empty()
    yield


# Create the FastAPI application object.
# title/version show up in the auto-generated docs at /docs.
app = FastAPI(
    title="AI Knowledge Assistant (RAG + SQL)",
    description="Ask your documents and databases anything, in any language.",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount the feature routers.
app.include_router(ask.router)        # /ask
app.include_router(upload.router)     # /upload (PDF ingestion)


@app.get("/")
def root():
    """Basic service info — confirms the API is reachable."""
    return {
        "service": "AI Knowledge Assistant (RAG + SQL)",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """
    Health check.

    Kubernetes (K3s) will call this as a liveness/readiness probe in Phase 7
    to decide whether the pod is alive and ready to receive traffic.
    Keep it cheap and dependency-free.
    """
    return {
        "status": "ok",
        "environment": settings.environment,
    }
