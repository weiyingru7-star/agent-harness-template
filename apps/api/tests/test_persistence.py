from fastapi.testclient import TestClient

from app.main import app
from core.db import session_scope
from core.db.models import (
    ArtifactRecord,
    ChunkRecord,
    DocumentRecord,
    FileRecord,
    RunEventRecord,
    RunRecord,
    StepRecord,
    TaskRecord,
)


client = TestClient(app)


def test_run_data_is_persisted() -> None:
    response = client.post("/api/runs", json={"input": "persist this run"})

    assert response.status_code == 201
    run_id = response.json()["id"]

    with session_scope() as session:
        assert session.get(RunRecord, run_id) is not None
        assert session.query(TaskRecord).count() == 1
        assert session.query(StepRecord).count() == 4
        assert session.query(RunEventRecord).count() == 11


def test_file_artifact_and_knowledge_data_are_persisted() -> None:
    run_id = client.post("/api/runs", json={"input": "persist related data"}).json()["id"]
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("notes.md", b"Agent Harness notes", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    artifact_response = client.post(
        f"/api/runs/{run_id}/artifacts",
        json={"file_id": file_id, "name": "Notes"},
    )
    ingest_response = client.post("/api/knowledge/ingest", json={"file_id": file_id})

    assert artifact_response.status_code == 201
    assert ingest_response.status_code == 201

    with session_scope() as session:
        file_record = session.get(FileRecord, file_id)
        artifact_record = session.get(ArtifactRecord, artifact_response.json()["id"])
        document_record = session.get(DocumentRecord, ingest_response.json()["document"]["id"])
        chunk_record = session.query(ChunkRecord).one()

        assert file_record is not None
        assert file_record.extension == ".md"
        assert artifact_record is not None
        assert artifact_record.title == "Notes"
        assert artifact_record.content == "Agent Harness notes"
        assert document_record is not None
        assert document_record.collection == "default"
        assert document_record.title == "notes.md"
        assert chunk_record.chunk_index == 0
