# ============================================================
# EMBEDDINGS HELPER (local, via sentence-transformers)
# Turns text into vectors (lists of numbers) that capture meaning.
# Shared by the FAQ service (Phase 2) and the RAG service (Phase 3),
# so the model is loaded ONCE and reused everywhere.
# ============================================================

from sentence_transformers import SentenceTransformer

from app.config import settings

# Module-level cache for the loaded model.
# Loading a model is expensive (reads ~80 MB from disk), so we do it
# lazily on first use and keep it for the life of the process.
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return the shared embedding model, loading it on first call."""
    global _model
    if _model is None:
        # settings.embeddings_model = "all-MiniLM-L6-v2" (small, fast, local)
        _model = SentenceTransformer(settings.embeddings_model)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of texts into a list of vectors.

    normalize_embeddings=True scales every vector to length 1, which means
    the cosine similarity between two vectors becomes a simple dot product
    (faster, and bounded between -1 and 1).
    """
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    # .tolist() converts the numpy array to plain Python lists.
    return vectors.tolist()
