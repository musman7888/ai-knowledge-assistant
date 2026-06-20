# ============================================================
# CONFIGURATION
# Loads all settings from environment variables (or a .env file).
# Centralizing config here means the rest of the code never reads
# os.environ directly — it just imports `settings`.
# ============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    pydantic-settings reads each field from an environment variable of the
    same (case-insensitive) name. Values in a local `.env` file are loaded
    automatically. Defaults below keep the app runnable before .env exists.
    """

    # --- LLM (via LiteLLM) ---
    llm_provider: str = "gemini"                 # gemini | openai | anthropic
    gemini_api_key: str = ""                     # filled from .env in real use
    llm_model: str = "gemini/gemini-1.5-flash"   # LiteLLM model string

    # --- Embeddings ---
    embeddings_provider: str = "local"           # local | openai | gemini
    embeddings_model: str = "all-MiniLM-L6-v2"   # local sentence-transformers model

    # --- Vector store (ChromaDB) ---
    chroma_dir: str = "./chroma_data"

    # --- Database (PostgreSQL, for Text-to-SQL) ---
    database_url: str = "postgresql://user:pass@localhost:5432/knowledge_db"

    # --- App ---
    api_secret_key: str = "change-me"
    environment: str = "development"             # development | production

    # Tell pydantic-settings to read from a .env file if present.
    # extra="ignore" so unrelated env vars don't raise errors.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# A single shared settings instance imported across the app.
# Created once at import time so the .env is read only once.
settings = Settings()
