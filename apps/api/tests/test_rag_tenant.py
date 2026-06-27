"""Tests for V1.4 RAG Tenant Filter.

Uses TestClient — tenant_id is optional for backward compatibility.
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ── Ingestion with tenant_id ───────────────────────────────────────


def test_ingest_with_tenant_id() -> None:
    """Document and chunk metadata carry tenant_id."""
    resp = client.post("/api/knowledge/documents", json={
        "title": "Tenant Doc",
        "text": "This document belongs to tenant t1.",
        "tenant_id": "t1",
    })
    assert resp.status_code == 201
    data = resp.json()
    doc = data["document"]
    assert doc["metadata"]["tenant_id"] == "t1"

    chunks = data["chunks"]
    assert len(chunks) >= 1
    for c in chunks:
        assert c["chunk_metadata"].get("tenant_id") == "t1"


def test_ingest_without_tenant_id() -> None:
    """Ingest without tenant_id works (backward compat)."""
    resp = client.post("/api/knowledge/documents", json={
        "title": "No Tenant Doc",
        "text": "This doc has no tenant.",
    })
    assert resp.status_code == 201
    data = resp.json()
    # metadata may be empty dict
    assert "tenant_id" not in data["document"].get("metadata", {})


def test_ingest_two_tenants() -> None:
    """Ingest documents for two different tenants."""
    for tenant in ("t1", "t2"):
        resp = client.post("/api/knowledge/documents", json={
            "title": f"Doc for {tenant}",
            "text": f"Confidential data for {tenant}.",
            "tenant_id": tenant,
        })
        assert resp.status_code == 201


# ── Retrieval with tenant filter ───────────────────────────────────


def test_retrieve_without_tenant_includes_all() -> None:
    """Default retrieval (no tenant_id) returns all chunks regardless of tenant."""
    client.post("/api/knowledge/documents", json={
        "title": "Shared",
        "text": "This belongs to t1.",
        "tenant_id": "t1",
    })
    resp = client.post("/api/knowledge/retrieve", json={
        "query": "belongs",
    })
    assert resp.status_code == 200
    assert len(resp.json()["results"]) >= 1


def test_retrieve_tenant_A_not_B() -> None:
    """Tenant A's retrieval does not see tenant B's chunks."""
    # Seed data for both tenants
    client.post("/api/knowledge/documents", json={
        "title": "T1 Secret", "text": "T1's confidential report data.",
        "tenant_id": "t1",
    })
    client.post("/api/knowledge/documents", json={
        "title": "T2 Secret", "text": "T2's confidential marketing data.",
        "tenant_id": "t2",
    })
    resp = client.post("/api/knowledge/retrieve", json={
        "query": "confidential",
        "tenant_id": "t1",
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert all(
        r["chunk"]["chunk_metadata"].get("tenant_id") == "t1"
        for r in results
    )


def test_retrieve_tenant_B_not_A() -> None:
    """Tenant B's retrieval does not see tenant A's chunks."""
    client.post("/api/knowledge/documents", json={
        "title": "T1 Secret", "text": "T1's secret project data.",
        "tenant_id": "t1",
    })
    client.post("/api/knowledge/documents", json={
        "title": "T2 Secret", "text": "T2's secret project data.",
        "tenant_id": "t2",
    })
    resp = client.post("/api/knowledge/retrieve", json={
        "query": "project",
        "tenant_id": "t2",
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert all(
        r["chunk"]["chunk_metadata"].get("tenant_id") == "t2"
        for r in results
    )


def test_retrieve_unknown_tenant_empty() -> None:
    """Unknown tenant returns no results."""
    client.post("/api/knowledge/documents", json={
        "title": "Test Doc",
        "text": "This doc belongs to t1.",
        "tenant_id": "t1",
    })
    resp = client.post("/api/knowledge/retrieve", json={
        "query": "belongs",
        "tenant_id": "unknown_tenant",
    })
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 0


# ── Backward compatibility ─────────────────────────────────────────


def test_old_create_document_still_works() -> None:
    """Old document creation without tenant_id still works."""
    resp = client.post("/api/knowledge/documents", json={
        "title": "Legacy Doc",
        "text": "This is a legacy document without tenant.",
    })
    assert resp.status_code == 201


def test_old_retrieve_still_works() -> None:
    """Old retrieval without tenant_id still works."""
    client.post("/api/knowledge/documents", json={
        "title": "Legacy Doc",
        "text": "This is a legacy document without tenant.",
    })
    resp = client.post("/api/knowledge/retrieve", json={
        "query": "legacy",
        "retrieval_mode": "keyword",
    })
    assert resp.status_code == 200
    assert len(resp.json()["results"]) >= 1


def test_all_retrieval_modes_with_tenant() -> None:
    """All three retrieval modes support tenant_id."""
    client.post("/api/knowledge/documents", json={
        "title": "T1 Doc",
        "text": "Tenant one confidential project alpha.",
        "tenant_id": "t1",
    })
    client.post("/api/knowledge/documents", json={
        "title": "T2 Doc",
        "text": "Tenant two confidential project beta.",
        "tenant_id": "t2",
    })
    for mode in ("keyword", "vector", "hybrid"):
        resp = client.post("/api/knowledge/retrieve", json={
            "query": "confidential project",
            "retrieval_mode": mode,
            "tenant_id": "t1",
        })
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["chunk"]["chunk_metadata"].get("tenant_id") == "t1"
