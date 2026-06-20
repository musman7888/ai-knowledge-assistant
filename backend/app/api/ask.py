# ============================================================
# /ask ENDPOINT
# The single entry point for questions. For now it routes to the FAQ
# service only; in Phase 5 the smart router will sit here and dispatch
# to FAQ / RAG / SQL. Keeping the request/response shape stable now means
# later modules slot in without changing the API contract.
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import faq_service, rag_service

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
    """
    Answer a question. For now: try FAQ first (fast, high precision), then
    fall back to RAG over uploaded documents. Phase 5 replaces this simple
    precedence with the smart router (FAQ / DB / DOCUMENT classification).
    """
    # 1) FAQ — cheap and confident when it matches.
    result = faq_service.find_answer(request.question)

    # 2) RAG — search uploaded documents if FAQ had no confident match.
    if result is None:
        result = rag_service.answer(request.question)

    # 3) Nothing available (no FAQ match, no documents ingested).
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
