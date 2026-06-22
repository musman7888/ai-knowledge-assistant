# ============================================================
# TRANSLATE SERVICE (multi-language)
# Strategy: translate the question INTO English, let the modules work in
# English, then translate the answer BACK to the user's language. This keeps
# FAQ / RAG / SQL English-only — only the edges deal with other languages.
# ============================================================

from app.services.llm_service import complete

# Separator used to return two values (language + text) from one LLM call.
_SEP = "|||"


def to_english(text: str) -> tuple[str, str]:
    """
    Detect the language of `text` and translate it to English.

    Returns (english_text, language_name). For English input, returns the
    text unchanged with language "en".
    """
    system = (
        "Detect the language of the user's text. "
        f"If it is English, reply exactly: en{_SEP}<the original text>. "
        f"Otherwise reply: <language name>{_SEP}<the English translation>. "
        f"Use '{_SEP}' as the separator and output nothing else."
    )
    reply = complete(text, system=system).strip()

    if _SEP in reply:
        lang, translated = reply.split(_SEP, 1)
        return translated.strip(), lang.strip()
    # If the model didn't follow the format, assume English (safe default).
    return text, "en"


def to_language(text: str, language: str) -> str:
    """Translate `text` into `language`. No-op if the target is English."""
    if language.lower() in ("en", "english"):
        return text
    system = f"Translate the user's text into {language}. Output only the translation."
    return complete(text, system=system).strip()
