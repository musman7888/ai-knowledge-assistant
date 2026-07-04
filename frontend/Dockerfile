# ============================================================
# Frontend image (Streamlit UI)
# Build from the REPO ROOT:
#   docker build -f frontend/Dockerfile -t ai-knowledge-frontend .
# ============================================================

FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY frontend/streamlit_app.py .

# BACKEND_URL is set at deploy time (in K3s it points at the backend service).
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]
