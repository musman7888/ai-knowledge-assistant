# ============================================================
# FASTAPI ENTRY POINT
# Creates the web application and defines the first two endpoints.
# Run locally:  uvicorn app.main:app --reload
# ============================================================

from fastapi import FastAPI

from app.config import settings

# Create the FastAPI application object.
# title/version show up in the auto-generated docs at /docs.
app = FastAPI(
    title="AI Knowledge Assistant (RAG + SQL)",
    description="Ask your documents and databases anything, in any language.",
    version="0.1.0",
)


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
