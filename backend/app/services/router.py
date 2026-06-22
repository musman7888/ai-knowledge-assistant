# ============================================================
# SMART ROUTER
# The brain that ties everything together. For each question:
#   1. translate to English (capture original language)
#   2. classify: DATABASE vs KNOWLEDGE
#   3. dispatch: DATABASE -> SQL; KNOWLEDGE -> FAQ then RAG
#   4. translate the answer back to the user's language
# All three engines return the same {answer, source, ...} shape, which is
# what lets this router treat them interchangeably.
# ============================================================

from app.prompts.system import CLASSIFY_PROMPT
from app.services import faq_service, rag_service, sql_service, translate
from app.services.llm_service import complete


def classify(question: str) -> str:
    """Return 'DATABASE' or 'KNOWLEDGE' for an (English) question."""
    reply = complete(question, system=CLASSIFY_PROMPT).strip().upper()
    # Be lenient: any mention of DATABASE counts as DATABASE, else KNOWLEDGE.
    return "DATABASE" if "DATABASE" in reply else "KNOWLEDGE"


def route(question: str) -> dict:
    """Answer a question, in the user's own language, using the right engine."""
    # 1) Normalize to English (and remember the original language).
    english_q, language = translate.to_english(question)

    # 2) Classify, then 3) dispatch.
    category = classify(english_q)
    if category == "DATABASE":
        result = sql_service.answer(english_q)
    else:
        # KNOWLEDGE: try the cheap, high-precision FAQ first, then documents.
        result = faq_service.find_answer(english_q) or rag_service.answer(english_q)

    # Nothing confident anywhere -> honest fallback.
    if result is None:
        result = {"answer": "I don't have information on that.", "source": "fallback"}

    # 4) Translate the answer back to the user's language.
    result["answer"] = translate.to_language(result["answer"], language)
    result["language"] = language
    return result
