# ============================================================
# /ask ENDPOINT
# The single entry point for questions. Delegates to the smart router,
# which classifies the question and dispatches to FAQ / RAG / SQL, with
# multi-language support. The endpoint stays thin — all logic is in services.
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.router import route

router = APIRouter()


class AskRequest(BaseModel):
    """Incoming question. Language is auto-detected by the router."""
    question: str
    language: str = "auto"


class AskResponse(BaseModel):
    """Uniform answer shape across all engines."""
    answer: str
    source: str                  # faq | document | database | fallback
    score: float | None = None   # FAQ match confidence, when available
    sql: str | None = None       # the SQL used, for database answers
    language: str | None = None  # detected language of the question


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Answer a question via the smart router (FAQ / RAG / SQL + multi-language)."""
    result = route(request.question)
    return AskResponse(
        answer=result["answer"],
        source=result.get("source", "fallback"),
        score=result.get("score"),
        sql=result.get("sql"),
        language=result.get("language"),
    )
