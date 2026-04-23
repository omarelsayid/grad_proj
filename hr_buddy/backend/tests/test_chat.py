"""Integration tests for the /chat and /health endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "index_ready" in data
    assert "chunks_count" in data


def test_chat_empty_message():
    resp = client.post("/chat", json={"message": ""})
    assert resp.status_code == 400


def test_chat_returns_structure():
    """If index is ready, /chat must return answer + citations."""
    health = client.get("/health").json()
    if not health["index_ready"]:
        pytest.skip("Index not ready — run /ingest-pdf first")

    resp = client.post("/chat", json={"message": "How many annual leave days do I get?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    if data["citations"]:
        cit = data["citations"][0]
        assert "page" in cit
        assert "snippet" in cit


def test_reset_index():
    resp = client.delete("/reset-index")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_not_found_graceful():
    """After reset, /chat should still return a graceful not-found answer."""
    client.delete("/reset-index")
    resp = client.post("/chat", json={"message": "What is the company's policy on time travel?"})
    # Should not 500 — may return 503 if collection is gone or a fallback answer
    assert resp.status_code in (200, 503)
