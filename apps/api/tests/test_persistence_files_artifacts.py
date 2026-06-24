from fastapi.testclient import TestClient

from app.main import app
from core.db import session_scope
from core.db.models import ArtifactRecord, FileRecord


client = TestClient(app)


def test_file_and_artifact_persistence_and_api_compatibility() -> None:
    run_id = client.post("/api/runs", json={"input": "persist related data"}).json()["id"]
    file_response = client.post(
        "/api/files/upload",
        files={"file": ("notes.md", b"Agent Harness notes", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    assert file_response.status_code == 201
    assert file_response.json()["extension"] == ".md"

    artifact_response = client.post(
        f"/api/runs/{run_id}/artifacts",
        json={"file_id": file_id, "name": "Notes"},
    )

    assert artifact_response.status_code == 201
    artifact = artifact_response.json()
    assert artifact["run_id"] == run_id
    assert artifact["file_id"] == file_id
    assert artifact["name"] == "Notes"
    assert artifact["kind"] == "text"
    assert artifact["text"] == "Agent Harness notes"

    with session_scope() as session:
        file_record = session.get(FileRecord, file_id)
        artifact_record = session.get(ArtifactRecord, artifact["id"])

        assert file_record is not None
        assert file_record.extension == ".md"
        assert file_record.metadata_ == {}
        assert artifact_record is not None
        assert artifact_record.title == "Notes"
        assert artifact_record.type == "text"
        assert artifact_record.content == "Agent Harness notes"
        assert artifact_record.metadata_ == {}
