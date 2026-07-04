# Unit tests for the text chunker (app/utils/chunking.py).

from app.utils.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_text_is_a_single_chunk():
    chunks = chunk_text("hello world", size=500, overlap=50)
    assert chunks == ["hello world"]


def test_chunks_respect_size():
    text = "a" * 1200
    chunks = chunk_text(text, size=500, overlap=50)
    # every chunk is at most `size` characters
    assert all(len(c) <= 500 for c in chunks)
    assert len(chunks) >= 2


def test_chunks_overlap():
    # 0..99 as two-digit numbers → predictable content
    text = "".join(f"{i:02d}" for i in range(100))  # 200 chars
    chunks = chunk_text(text, size=100, overlap=20)
    # second chunk starts 80 chars in, so it shares the last 20 chars of chunk 1
    assert chunks[0][-20:] == chunks[1][:20]


def test_whitespace_only_chunks_are_skipped():
    text = "abc" + " " * 100 + "def"
    chunks = chunk_text(text, size=50, overlap=0)
    assert all(c.strip() for c in chunks)
    assert "abc" in chunks[0]
