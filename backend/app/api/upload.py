# ============================================================
# /upload ENDPOINT
# Accepts a PDF file, extracts its text, and ingests it into the
# vector store (ChromaDB) so it can be queried later via /ask.
# This is the "setup" step a document owner does once per document.
# ============================================================

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import rag_service

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    """Upload a PDF -> extract text -> chunk + embed + store. Returns chunk count."""
    # Basic validation: only accept PDFs (per CONSTITUTION security note).
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # pypdf reads from a path, so write the upload to a temp file first.
    contents = await file.read()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        text = rag_service.extract_text(tmp_path)
        chunks_stored = rag_service.ingest(doc_id=file.filename, text=text)
    finally:
        # Always clean up the temp file, even if ingestion fails.
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    if chunks_stored == 0:
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from this PDF.",
        )

    return {"filename": file.filename, "chunks_stored": chunks_stored}
