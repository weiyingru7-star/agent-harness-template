from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _setup_docs() -> None:
    """Create test documents before each test."""
    texts = [
        ("Runtime Traces", "Runtime traces record ordered execution events for each agent step."),
        ("Checkpoint Store", "Checkpoints store state snapshots after each completed node."),
        ("Tool Call Args", "Tool calls include arguments, result, status and error details."),
    ]
    for title, text in texts:
        client.post("/api/knowledge/documents", json={"title": title, "text": text})


def test_default_retrieval_mode_is_keyword() -> None:
    resp = client.post("/api/knowledge/retrieve", json={"query": "traces"})

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1
    for r in results:
        assert r.get("retrieval_mode") == "keyword"
        assert r.get("score_type") == "term_frequency"


def test_keyword_mode_explicit() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "checkpoints", "retrieval_mode": "keyword"},
    )

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1


def test_vector_mode_returns_results() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "state snapshots", "retrieval_mode": "vector"},
    )

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1


def test_vector_mode_has_citation() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "execution", "retrieval_mode": "vector", "limit": 3},
    )

    assert resp.status_code == 200
    result = resp.json()["results"][0]
    assert result["citation"]["document_id"]
    assert result["citation"]["score"] >= 0
    assert result["citation"]["quote"]


def test_vector_mode_score_type() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "tool", "retrieval_mode": "vector"},
    )

    assert resp.status_code == 200
    for r in resp.json()["results"]:
        assert r["retrieval_mode"] == "vector"
        assert r["score_type"] == "cosine"


def test_hybrid_mode_returns_results() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "argumants", "retrieval_mode": "hybrid"},
    )

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1


def test_hybrid_mode_no_duplicates() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "checkpoints", "retrieval_mode": "hybrid", "limit": 5},
    )

    assert resp.status_code == 200
    results = resp.json()["results"]
    chunk_ids = [r["chunk"]["id"] for r in results]
    assert len(chunk_ids) == len(set(chunk_ids))


def test_retrieve_response_has_metadata() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "traces", "retrieval_mode": "keyword"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert "metadata" in body
    assert body["metadata"]["retrieval_mode"] == "keyword"
    assert body["metadata"]["score_type"] == "term_frequency"


def test_retrieve_response_metadata_vector() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "events", "retrieval_mode": "vector"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["metadata"]["retrieval_mode"] == "vector"
    assert body["metadata"]["score_type"] == "cosine"


def test_unknown_retrieval_mode_errors() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "test", "retrieval_mode": "unknown_mode"},
    )

    assert resp.status_code == 400


def test_vector_mode_with_collection_filter() -> None:
    resp = client.post(
        "/api/knowledge/retrieve",
        json={"query": "traces", "retrieval_mode": "vector", "collection": "default"},
    )

    assert resp.status_code == 200
    assert len(resp.json()["results"]) >= 1


def test_keyword_and_vector_modes_independent() -> None:
    kw = client.post(
        "/api/knowledge/retrieve",
        json={"query": "execution", "retrieval_mode": "keyword"},
    )
    vec = client.post(
        "/api/knowledge/retrieve",
        json={"query": "execution", "retrieval_mode": "vector"},
    )

    assert kw.status_code == 200
    assert vec.status_code == 200
    # Both return results, potentially different order / scores
    assert len(kw.json()["results"]) >= 1
    assert len(vec.json()["results"]) >= 1
