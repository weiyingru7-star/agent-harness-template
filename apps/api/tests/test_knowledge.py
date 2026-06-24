from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ingest_documents_and_retrieve_with_citation() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("notes.md", b"Agent Harness notes", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert ingest_response.status_code == 201
    ingested = ingest_response.json()
    assert ingested["document"]["file_id"] == file_id
    assert ingested["chunks"][0]["text"] == "Agent Harness notes"

    documents_response = client.get("/api/knowledge/documents")

    assert documents_response.status_code == 200
    assert documents_response.json()[0]["id"] == ingested["document"]["id"]

    retrieve_response = client.post(
        "/api/knowledge/retrieve",
        json={"query": "Harness", "limit": 3},
    )

    assert retrieve_response.status_code == 200
    result = retrieve_response.json()["results"][0]
    assert result["chunk"]["text"] == "Agent Harness notes"
    assert result["citation"]["document_id"] == ingested["document"]["id"]
    assert result["citation"]["file_id"] == file_id


def test_ingest_unknown_file_returns_404() -> None:
    response = client.post("/api/knowledge/ingest", json={"file_id": "file_missing"})

    assert response.status_code == 404
