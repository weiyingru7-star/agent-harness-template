from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ingest_has_enhanced_document_fields() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("rag.md", b"# RAG Pipeline\n\nRetrieval augmented generation.", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert ingest_response.status_code == 201
    doc = ingest_response.json()["document"]
    assert doc["collection"] == "default"
    assert doc["title"] == "rag.md"
    assert doc["source"] == "file"
    assert doc["content_type"] == "text/markdown"


def test_ingest_has_enhanced_chunk_fields() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("stats.md", b"Line one\n\nLine two\n\nLine three", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert ingest_response.status_code == 201
    chunks = ingest_response.json()["chunks"]
    assert len(chunks) > 0
    chunk = chunks[0]
    assert chunk["char_count"] > 0
    assert chunk["token_count"] > 0
    assert chunk["index"] == 0


def test_enhanced_citation_in_retrieve() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("cite.md", b"Agent Harness is a template for building AI agents.", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    client.post("/api/knowledge/ingest", json={"file_id": file_id})
    retrieve_response = client.post(
        "/api/knowledge/retrieve",
        json={"query": "Harness", "limit": 3},
    )

    assert retrieve_response.status_code == 200
    result = retrieve_response.json()["results"][0]
    citation = result["citation"]
    assert citation["title"] is not None
    assert citation["source"] == "file"
    assert citation["score"] > 0
    assert citation["collection"] == "default"


def test_get_document_by_id() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("doc.md", b"Single document test.", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})
    doc_id = ingest_response.json()["document"]["id"]

    doc_response = client.get(f"/api/knowledge/documents/{doc_id}")

    assert doc_response.status_code == 200
    doc = doc_response.json()
    assert doc["id"] == doc_id
    assert doc["collection"] == "default"


def test_get_collection_chunks() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("col.md", b"Collection chunk test.", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    client.post("/api/knowledge/ingest", json={"file_id": file_id})
    chunks_response = client.get("/api/knowledge/collections/default/chunks")

    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) > 0
    assert chunks[0]["collection"] == "default"


def test_get_missing_document_returns_404() -> None:
    response = client.get("/api/knowledge/documents/doc_missing")

    assert response.status_code == 404


def test_ingested_chunks_have_correct_index_order() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("multi.md", b"Para A\n\nPara B\n\nPara C\n\nPara D", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert ingest_response.status_code == 201
    chunks = ingest_response.json()["chunks"]
    indices = [chunk["index"] for chunk in chunks]
    assert indices == sorted(indices)
