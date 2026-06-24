from fastapi.testclient import TestClient

from app.main import app
from core.db import session_scope
from core.db.models import ChunkRecord, DocumentRecord


client = TestClient(app)


def test_knowledge_persistence_and_retrieve_citation() -> None:
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("notes.md", b"Agent Harness notes", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert ingest_response.status_code == 201
    document_id = ingest_response.json()["document"]["id"]
    assert ingest_response.json()["chunks"][0]["text"] == "Agent Harness notes"

    retrieve_response = client.post(
        "/api/knowledge/retrieve",
        json={"query": "Harness", "limit": 3},
    )

    assert retrieve_response.status_code == 200
    result = retrieve_response.json()["results"][0]
    assert result["citation"]["document_id"] == document_id
    assert result["citation"]["file_id"] == file_id
    assert result["citation"]["chunk_index"] == 0

    with session_scope() as session:
        document_record = session.get(DocumentRecord, document_id)
        chunk_record = session.query(ChunkRecord).one()

        assert document_record is not None
        assert document_record.collection == "default"
        assert document_record.title == "notes.md"
        assert document_record.source == "file"
        assert document_record.metadata_ == {}
        assert chunk_record.document_id == document_id
        assert chunk_record.chunk_index == 0
        assert chunk_record.metadata_ == {}
