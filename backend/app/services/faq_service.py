# ============================================================
# FAQ SERVICE
# Answers a question by finding the most semantically similar FAQ entry.
# Uses embeddings (meaning-based match), so paraphrased questions still
# match — e.g. "how do I get my money back?" -> "What is your return policy?"
# ============================================================

import json
from pathlib import Path

from app.config import settings
from app.services.embeddings import embed

# Path to faqs.json — via settings.data_dir so it works both locally and in
# the container (where the Dockerfile sets DATA_DIR=/app/data).
FAQ_PATH = Path(settings.data_dir) / "faqs.json"

# Minimum similarity (0..1) for a match to count. Starting suggestion;
# tune in the Learn by Doing task below.
SIMILARITY_THRESHOLD = 0.45

# --- Load FAQs and pre-compute their question embeddings once at import ---
with open(FAQ_PATH, encoding="utf-8") as f:
    _faqs: list[dict] = json.load(f)

# Embed "question + answer" together (not just the question). The answer's
# content matters: a user asking about "money back" should match an answer
# that mentions "full refund", even though the question wording differs.
# We pre-compute these once so each request only embeds the user's question.
_corpus = [f"{item['question']} {item['answer']}" for item in _faqs]
_entry_vectors = embed(_corpus) if _faqs else []


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Vectors are normalized, so this is just a dot product."""
    return sum(x * y for x, y in zip(a, b))


def find_answer(question: str) -> dict | None:
    """
    Find the best-matching FAQ answer for `question`.

    Returns a dict {answer, source, score, matched_question} if a good match
    is found, otherwise None (so the router can fall back later).
    """
    if not _faqs:
        return None

    # Embed the incoming question and score it against every FAQ entry.
    query_vec = embed([question])[0]
    scores = [_cosine(query_vec, vec) for vec in _entry_vectors]

    # Pick the FAQ with the highest similarity to the question.
    best_index = max(range(len(scores)), key=lambda i: scores[i])
    best_score = scores[best_index]

    # Only answer if we're confident enough; otherwise defer (None) so the
    # router can fall back to "I don't have information on that."
    if best_score < SIMILARITY_THRESHOLD:
        return None

    return {
        "answer": _faqs[best_index]["answer"],
        "source": "faq",
        "score": round(best_score, 3),
        "matched_question": _faqs[best_index]["question"],
    }
