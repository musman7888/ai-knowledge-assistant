# ============================================================
# Backend image (FastAPI + RAG/SQL/FAQ)
# Build from the REPO ROOT (needs both backend/ and data/):
#   docker build -f backend/Dockerfile -t ai-knowledge-backend .
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch first so pip doesn't pull the huge CUDA build
# (sentence-transformers depends on torch; this keeps the image much smaller).
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 \
        torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

# Bake the embedding model into the image so the container never downloads
# it at runtime (no network dependency / flaky-download risk at startup).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Application code and bundled data (faqs.json, sample.pdf).
COPY backend/app ./app
COPY data ./data

# DATA_DIR points at the copied data; CHROMA_DIR is a writable path (a PVC
# will be mounted here in K3s so the vector store survives restarts).
ENV DATA_DIR=/app/data \
    CHROMA_DIR=/app/chroma_data \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
