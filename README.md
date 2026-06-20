# AI Knowledge Assistant (RAG + SQL)

> Ask your documents and databases anything, in any language.

A multi-source AI assistant: one chat box, a smart router, and four answer engines —
**Document Q&A (RAG)**, **Database Q&A (Text-to-SQL)**, **FAQ search**, and
**multi-language** — with an honest "I don't have information on that" fallback.

> 🚧 **Status:** Under development (Phase 1 — Foundation). This README is a placeholder
> and will be expanded with features, screenshots, demo, and setup as the project grows.

## Tech stack
Python · FastAPI · LiteLLM (Gemini) · sentence-transformers · ChromaDB · PostgreSQL ·
Streamlit · Docker · Helm · K3s · GitHub Actions

## Project layout
```
backend/    FastAPI app (api, services, prompts, utils)
frontend/   Streamlit UI
data/       Sample PDF, FAQs, CSVs
db/         PostgreSQL schema + import
helm/       Kubernetes deployment chart
docs/       Architecture & setup docs
```
