from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_get_run_artifact() -> None:
    run_response = client.post("/api/runs", json={"input": "artifact run"})
    run_id = run_response.json()["id"]

    file_response = client.post(
        "/api/files/upload",
        files={"file": ("artifact.md", b"artifact text", "text/markdown")},
    )
    file_id = file_response.json()["id"]

    artifact_response = client.post(
        f"/api/runs/{run_id}/artifacts",
        json={"file_id": file_id, "name": "Artifact notes"},
    )

    assert artifact_response.status_code == 201
    artifact = artifact_response.json()
    assert artifact["id"].startswith("artifact_")
    assert artifact["run_id"] == run_id
    assert artifact["file_id"] == file_id
    assert artifact["name"] == "Artifact notes"
    assert artifact["kind"] == "text"
    assert artifact["text"] == "artifact text"

    list_response = client.get(f"/api/runs/{run_id}/artifacts")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == artifact["id"]

    get_response = client.get(f"/api/artifacts/{artifact['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == artifact["id"]


def test_create_artifact_for_unknown_run_returns_404() -> None:
    response = client.post(
        "/api/runs/run_missing/artifacts",
        json={"file_id": "file_missing", "name": "Missing"},
    )

    assert response.status_code == 404
