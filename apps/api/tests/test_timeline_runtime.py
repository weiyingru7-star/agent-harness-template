from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_run_timeline_returns_completed_steps() -> None:
    run = client.post("/api/runs", json={"input": "timeline success"}).json()

    response = client.get(f"/api/runs/{run['id']}/timeline")

    assert response.status_code == 200
    timeline = response.json()
    assert timeline["run_id"] == run["id"]
    assert timeline["trace_id"] == run["trace_id"]
    assert timeline["status"] == "completed"
    assert timeline["items"]

    step_items = [item for item in timeline["items"] if item["type"] == "step"]
    assert [item["metadata"]["step_name"] for item in step_items] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
    assert all(item["status"] == "completed" for item in step_items)
    assert all(item["sequence"] is not None for item in step_items)
    assert all(item["duration_ms"] is not None for item in step_items)
    assert all(item["checkpoint_id"] for item in step_items)
    assert [item["checkpoint_index"] for item in step_items] == [1, 2, 3, 4]


def test_failed_run_timeline_contains_failed_item() -> None:
    run = client.post("/api/runs", json={"input": "timeline __fail__"}).json()

    response = client.get(f"/api/runs/{run['id']}/timeline")

    assert response.status_code == 200
    timeline = response.json()
    assert timeline["status"] == "failed"

    step_items = [item for item in timeline["items"] if item["type"] == "step"]
    assert [item["metadata"]["step_name"] for item in step_items] == [
        "input_node",
        "skill_node",
    ]
    failed_item = step_items[-1]
    assert failed_item["status"] == "failed"
    assert failed_item["metadata"]["step_name"] == "skill_node"
    assert failed_item["error_type"] == "DemoAgentTestFailure"
    assert failed_item["error_message"] == "demo_agent test failure triggered by __fail__"
    assert failed_item["checkpoint_id"] is None


def test_timeline_does_not_break_events_trace_checkpoints_or_retry() -> None:
    failed_run = client.post("/api/runs", json={"input": "timeline retry __fail__"}).json()

    assert client.get(f"/api/runs/{failed_run['id']}/timeline").status_code == 200
    assert client.get(f"/api/runs/{failed_run['id']}/events").status_code == 200
    assert client.get(f"/api/runs/{failed_run['id']}/trace").status_code == 200
    assert client.get(f"/api/runs/{failed_run['id']}/checkpoints").status_code == 200

    retry_response = client.post(f"/api/runs/{failed_run['id']}/retry")
    assert retry_response.status_code == 201
    retry_run = retry_response.json()

    timeline = client.get(f"/api/runs/{retry_run['id']}/timeline").json()
    assert timeline["run_id"] == retry_run["id"]
    assert any(item["type"] == "retry" for item in timeline["items"])


def test_unknown_run_timeline_returns_404() -> None:
    response = client.get("/api/runs/run_missing/timeline")

    assert response.status_code == 404
