# ============================================================
# TEXT CHUNKING (pure — no external dependencies)
# Splits a long string into overlapping chunks for RAG ingestion.
# Kept dependency-free so it's easy to unit-test in isolation.
# ============================================================

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # characters shared between consecutive chunks


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split `text` into overlapping chunks of ~`size` characters.

    Each chunk starts `size - overlap` characters after the previous one, so a
    sentence split across a boundary still appears whole in one chunk.
    Empty/whitespace-only chunks are skipped.
    """
    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(text), step):
        chunk = text[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks
