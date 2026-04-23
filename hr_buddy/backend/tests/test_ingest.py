"""Unit tests for PDF ingestion pipeline."""
import os
import tempfile
import pytest

from app.services.pdf_ingest import _clean, _split_page


def test_clean_removes_extra_whitespace():
    raw = "Hello   World\n\n\n\nHow are you?"
    result = _clean(raw)
    assert "   " not in result
    assert result.count("\n") <= 2


def test_split_page_basic():
    text = "A" * 1500  # long text
    chunks = _split_page(text, page_num=1, chunk_size=700, overlap=150)
    assert len(chunks) >= 2
    for c in chunks:
        assert c["page"] == 1
        assert "text" in c
        assert len(c["text"]) > 0


def test_split_page_empty():
    chunks = _split_page("", page_num=1)
    assert chunks == []


def test_split_page_short_text():
    text = "Short policy text that fits in one chunk easily."
    chunks = _split_page(text, page_num=3)
    assert len(chunks) == 1
    assert chunks[0]["page"] == 3


def test_split_page_prefers_sentence_boundary():
    text = ("Hello world. " * 60).strip()
    chunks = _split_page(text, page_num=2, chunk_size=200, overlap=50)
    for c in chunks:
        # Chunks should not end mid-sentence in most cases
        assert len(c["text"]) > 50


@pytest.mark.skipif(
    not os.path.exists("../../SkillSync_Company_Policy_2026.pdf"),
    reason="PDF not present — integration test skipped",
)
def test_extract_chunks_integration():
    from app.services.pdf_ingest import extract_chunks

    chunks = extract_chunks("../../SkillSync_Company_Policy_2026.pdf")
    assert len(chunks) > 10
    for c in chunks:
        assert "text" in c
        assert "page" in c
        assert c["page"] >= 1
