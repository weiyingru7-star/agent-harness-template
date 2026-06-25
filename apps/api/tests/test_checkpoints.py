from fastapi.testclient import TestClient

from app.main import app
from core.db import session_scope
from core.db.models import CheckpointRecord


client = TestClient(app)


def test_run_creates_checkpoints() -> None:
    response = client.post("/api/runs", json={"input": "checkpoint please"})

    assert response.status_code == 201
    run = response.json()
    run_id = run["id"]

    checkpoints_response = client.get(f"/api/runs/{run_id}/checkpoints")

    assert checkpoints_response.status_code == 200
    checkpoints = checkpoints_response.json()
    assert len(checkpoints) == 4
    assert [checkpoint["checkpoint_index"] for checkpoint in checkpoints] == [1, 2, 3, 4]
    assert [checkpoint["metadata"]["step_name"] for checkpoint in checkpoints] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
    assert all(checkpoint["run_id"] == run_id for checkpoint in checkpoints)
    assert all(checkpoint["trace_id"] == run["trace_id"] for checkpoint in checkpoints)
    assert all(checkpoint["span_id"].startswith("span_") for checkpoint in checkpoints)
    assert checkpoints[0]["state"]["normalized_input"] == "checkpoint please"
    assert checkpoints[-1]["state"]["final_output"].startswith("demo_agent mock response")

    with session_scope() as session:
        assert session.query(CheckpointRecord).filter_by(run_id=run_id).count() == 4


def test_get_checkpoint_by_id() -> None:
    run = client.post("/api/runs", json={"input": "checkpoint lookup"}).json()
    checkpoints = client.get(f"/api/runs/{run['id']}/checkpoints").json()
    checkpoint_id = checkpoints[0]["id"]

    response = client.get(f"/api/checkpoints/{checkpoint_id}")

    assert response.status_code == 200
    checkpoint = response.json()
    assert checkpoint["id"] == checkpoint_id
    assert checkpoint["run_id"] == run["id"]
    assert checkpoint["checkpoint_index"] == 1


def test_checkpoint_routes_return_404_for_unknown_ids() -> None:
    run_response = client.get("/api/runs/run_missing/checkpoints")
    checkpoint_response = client.get("/api/checkpoints/checkpoint_missing")

    assert run_response.status_code == 404
    assert run_response.json()["detail"] == "Run not found"
    assert checkpoint_response.status_code == 404
    assert checkpoint_response.json()["detail"] == "Checkpoint not found"


def test_events_and_trace_still_work_with_checkpoints() -> None:
    run = client.post("/api/runs", json={"input": "checkpoint compatibility"}).json()

    events_response = client.get(f"/api/runs/{run['id']}/events")
    trace_response = client.get(f"/api/runs/{run['id']}/trace")

    assert events_response.status_code == 200
    assert trace_response.status_code == 200
    assert events_response.json()[0]["event_type"] == "run.created"
    assert len(trace_response.json()["spans"]) == 4
