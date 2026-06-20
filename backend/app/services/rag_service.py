# ============================================================
# RAG SERVICE — ingestion half (Phase 3a)
# Turns an uploaded PDF into searchable knowledge:
#   PDF -> extract text -> split into chunks -> embed -> store in ChromaDB
# Retrieval + answering is added in Phase 3b.
# ============================================================

import chromadb
import pypdf

from app.config import settings
from app.services.embeddings import embed

# Persistent ChromaDB client: vectors are written to disk at CHROMA_DIR so
# they survive restarts (unlike the in-memory FAQ approach). In K3s this
# directory will live on a PersistentVolumeClaim (Phase 7).
_client = chromadb.PersistentClient(path=settings.chroma_dir)
# A "collection" is like a table for vectors. All document chunks go here.
_collection = _client.get_or_create_collection("documents")

# Chunking parameters (tune in the Learn by Doing task).
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # characters shared between consecutive chunks


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    reader = pypdf.PdfReader(pdf_path)
    # extract_text() can return None for image-only pages, so guard with "".
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str) -> list[str]:
    """
    Split `text` into overlapping chunks of ~CHUNK_SIZE characters.

    Each chunk overlaps the previous by CHUNK_OVERLAP characters so a
    sentence split across a boundary still appears whole in one chunk.
    """
    chunks: list[str] = []
    # Step forward by (size - overlap) so windows overlap, not abut.
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(text), step):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:                       # skip empty/whitespace-only slices
            chunks.append(chunk)
    return chunks


def ingest(doc_id: str, text: str) -> int:
    """
    Chunk, embed, and store a document's text in ChromaDB.
    Returns the number of chunks stored.
    """
    chunks = chunk_text(text)
    if not chunks:
        return 0

    # Embed all chunks at once (reuses the shared, cached model).
    vectors = embed(chunks)

    # Unique id per chunk so re-ingesting the same doc overwrites cleanly.
    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

    # upsert (not add) so re-uploading a file doesn't error on duplicate ids.
    _collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


def count() -> int:
    """Total number of chunks currently stored (for testing/debugging)."""
    return _collection.count()
