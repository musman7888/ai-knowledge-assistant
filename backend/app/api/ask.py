# ============================================================
# /ask ENDPOINT
# The single entry point for questions. For now it routes to the FAQ
# service only; in Phase 5 the smart router will sit here and dispatch
# to FAQ / RAG / SQL. Keeping the request/response shape stable now means
# later modules slot in without changing the API contract.
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import faq_service

router = APIRouter()


class AskRequest(BaseModel):
    """Incoming question. `language` is reserved for Phase 5 (multi-language)."""
    question: str
    language: str = "auto"


class AskResponse(BaseModel):
    """Uniform answer shape every module conforms to."""
    answer: str
    source: str                 # "faq" | "fallback" (later: "document" | "database")
    score: float | None = None  # match confidence, when available


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Answer a question. Currently FAQ-only."""
    result = faq_service.find_answer(request.question)

    # No confident match -> honest fallback (per CONSTITUTION).
    if result is None:
        return AskResponse(
            answer="I don't have information on that.",
            source="fallback",
        )

    return AskResponse(
        answer=result["answer"],
        source=result["source"],
        score=result.get("score"),
    )
