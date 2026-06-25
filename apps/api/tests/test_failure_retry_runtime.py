from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_normal_run_still_completes() -> None:
    response = client.post("/api/runs", json={"input": "normal path"})

    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "completed"
    assert run["error_type"] is None
    assert run["error_message"] is None
    assert run["failed_at"] is None


def test_failure_run_records_failed_step_and_events() -> None:
    response = client.post("/api/runs", json={"input": "please __fail__ now"})

    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "failed"
    assert run["error_type"] == "DemoAgentTestFailure"
    assert run["error_message"] == "demo_agent test failure triggered by __fail__"
    assert run["failed_at"] is not None

    failed_steps = [step for step in run["steps"] if step["status"] == "failed"]
    assert len(failed_steps) == 1
    failed_step = failed_steps[0]
    assert failed_step["name"] == "skill_node"
    assert failed_step["attempt"] == 1
    assert failed_step["max_attempts"] == 1
    assert failed_step["error_type"] == "DemoAgentTestFailure"
    assert failed_step["error_message"] == "demo_agent test failure triggered by __fail__"
    assert failed_step["failed_at"] is not None

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "step.failed" in event_types
    assert "run.failed" in event_types


def test_failed_run_trace_and_checkpoints_remain_available() -> None:
    run = client.post("/api/runs", json={"input": "trace __fail__"}).json()

    events_response = client.get(f"/api/runs/{run['id']}/events")
    trace_response = client.get(f"/api/runs/{run['id']}/trace")
    checkpoints_response = client.get(f"/api/runs/{run['id']}/checkpoints")

    assert events_response.status_code == 200
    assert trace_response.status_code == 200
    assert checkpoints_response.status_code == 200
    assert [span["name"] for span in trace_response.json()["spans"]] == [
        "input_node",
        "skill_node",
    ]
    checkpoints = checkpoints_response.json()
    assert len(checkpoints) == 1
    assert checkpoints[0]["metadata"]["step_name"] == "input_node"


def test_retry_failed_run_creates_new_run_with_metadata_and_events() -> None:
    failed_run = client.post("/api/runs", json={"input": "retry __fail__"}).json()

    response = client.post(f"/api/runs/{failed_run['id']}/retry")

    assert response.status_code == 201
    retry_run = response.json()
    assert retry_run["id"] != failed_run["id"]
    assert retry_run["metadata"]["retry_of_run_id"] == failed_run["id"]
    assert retry_run["metadata"]["attempt"] == 2
    assert retry_run["status"] == "failed"

    events = client.get(f"/api/runs/{retry_run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "run.retry_started" in event_types
    assert "step.failed" in event_types
    assert "run.failed" in event_types


def test_retry_rejects_unknown_and_non_failed_runs() -> None:
    missing_response = client.post("/api/runs/run_missing/retry")
    completed_run = client.post("/api/runs", json={"input": "cannot retry"}).json()
    completed_response = client.post(f"/api/runs/{completed_run['id']}/retry")

    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Run not found"
    assert completed_response.status_code == 400
    assert completed_response.json()["detail"] == "Only failed runs can be retried"
