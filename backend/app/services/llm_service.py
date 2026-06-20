# ============================================================
# LLM SERVICE (provider-agnostic via LiteLLM)
# The ONE place the whole app talks to a language model.
# Every feature (FAQ, RAG answers, SQL generation, translation)
# calls complete() here — so switching Gemini -> OpenAI -> Claude
# is a config change in .env, not a code change.
# ============================================================

import litellm

from app.config import settings


class LLMError(Exception):
    """Raised when an LLM request fails, so callers catch one known type."""


def _build_messages(prompt: str, system: str | None) -> list[dict]:
    """
    Turn a prompt (and optional system instruction) into the
    chat-message format every LLM provider expects.

    - "system" sets the model's role/behavior (optional)
    - "user" carries the actual question/prompt
    """
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def complete(prompt: str, system: str | None = None) -> str:
    """
    Send a prompt to the configured LLM and return the text answer.

    Args:
        prompt: The user/question text.
        system: Optional system instruction (e.g. "You are a SQL expert").

    Returns:
        The model's reply as a plain string.
    """
    messages = _build_messages(prompt, system)

    try:
        # LiteLLM normalizes every provider behind one call.
        # settings.llm_model looks like "gemini/gemini-1.5-flash".
        response = litellm.completion(
            model=settings.llm_model,
            messages=messages,
            api_key=settings.gemini_api_key,
        )
        # LiteLLM returns an OpenAI-style object; the text lives here.
        return response.choices[0].message.content

    except Exception as error:
        # Log the real cause for debugging (type only — never the API key).
        print(f"[llm_service] LLM call failed: {type(error).__name__}: {error}")
        # Re-raise as our own clean type. "from error" keeps the original
        # traceback for logs, but callers only need to catch LLMError.
        raise LLMError("The AI service request failed. Please try again.") from error
