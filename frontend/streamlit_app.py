# ============================================================
# STREAMLIT FRONTEND
# A thin chat UI over the FastAPI backend. It only does two things:
# upload a PDF (POST /upload) and ask questions (POST /ask). All the
# intelligence lives in the backend — this is just a "mouth".
# Run:  streamlit run streamlit_app.py
# ============================================================

import os

import requests
import streamlit as st

# Backend location — overridable for K3s/prod via env var.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Friendly label + emoji per answer source.
SOURCE_BADGES = {
    "faq": "🟢 FAQ",
    "document": "🔵 Document (RAG)",
    "database": "🟠 Database (SQL)",
    "fallback": "⚪ No match",
    "error": "🔴 Error",
}

st.set_page_config(page_title="AI Knowledge Assistant", page_icon="🧠")

# Put our logo + title INSIDE Streamlit's own top bar (stHeader), which the
# framework already keeps fixed at the top. Injecting a separate fixed element
# gets clipped by Streamlit's transformed containers, but styling stHeader and
# adding our title via ::before is reliable — it never scrolls.
st.markdown(
    """
    <style>
      [data-testid="stHeader"] {
        background: var(--background-color) !important;
        height: 3.6rem;
        z-index: 1000;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
      }
      [data-testid="stHeader"]::before {
        content: "🧠  AI Knowledge Assistant";
        position: absolute; left: 1.25rem; top: 50%;
        transform: translateY(-50%);
        font-size: 1.3rem; font-weight: 600;
        color: var(--text-color, #31333F);
        white-space: nowrap;
      }
      .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.caption("Ask your documents and databases anything, in any language.")


def render_answer(data: dict) -> None:
    """Show the answer plus source badge, language, confidence, and SQL."""
    st.markdown(data.get("answer", ""))

    bits = [f"**Source:** {SOURCE_BADGES.get(data.get('source'), data.get('source'))}"]
    if data.get("language"):
        bits.append(f"**Language:** {data['language']}")
    if data.get("score") is not None:
        bits.append(f"**Confidence:** {data['score']}")
    st.caption("  •  ".join(bits))

    # For database answers, let the user inspect the exact query (trust signal).
    if data.get("sql"):
        with st.expander("SQL used"):
            st.code(data["sql"], language="sql")


# --- Sidebar: document upload (the one-time "setup" step) ---
with st.sidebar:
    st.header("📄 Upload a document")
    pdf = st.file_uploader("Choose a PDF", type=["pdf"])
    if pdf is not None and st.button("Upload to knowledge base"):
        with st.spinner("Ingesting..."):
            try:
                files = {"file": (pdf.name, pdf.getvalue(), "application/pdf")}
                resp = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=180)
                if resp.ok:
                    info = resp.json()
                    st.success(f"Stored {info['chunks_stored']} chunks from {info['filename']}")
                else:
                    st.error(resp.json().get("detail", "Upload failed"))
            except Exception as exc:
                st.error(f"Could not reach backend: {exc}")
    st.caption(f"Backend: {BACKEND_URL}")


# --- Chat history (kept in the session) ---
if "history" not in st.session_state:
    st.session_state.history = []

# Replay past turns on each rerun.
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_answer(msg["data"])
        else:
            st.markdown(msg["content"])


# --- New question ---
question = st.chat_input("Ask a question...")
if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"question": question},
                    timeout=120,
                )
                data = resp.json()
            except Exception as exc:
                data = {"answer": f"Could not reach backend: {exc}", "source": "error"}
        render_answer(data)

    st.session_state.history.append({"role": "assistant", "content": data.get("answer", ""), "data": data})
