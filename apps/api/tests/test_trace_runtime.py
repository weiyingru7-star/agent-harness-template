from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_run_generates_trace_and_spans() -> None:
    response = client.post("/api/runs", json={"input": "trace please"})

    assert response.status_code == 201
    run = response.json()
    assert run["trace_id"].startswith("trace_")
    assert [step["type"] for step in run["steps"]] == ["node", "node", "node", "node"]
    assert all(step["trace_id"] == run["trace_id"] for step in run["steps"])
    assert all(step["span_id"].startswith("span_") for step in run["steps"])
    assert all(step["started_at"] is not None for step in run["steps"])
    assert all(step["ended_at"] is not None for step in run["steps"])
    assert all(step["duration_ms"] is not None for step in run["steps"])


def test_run_events_remain_compatible_and_include_typed_fields() -> None:
    create_response = client.post("/api/runs", json={"input": "events trace"})
    run = create_response.json()

    response = client.get(f"/api/runs/{run['id']}/events")

    assert response.status_code == 200
    events = response.json()
    assert events[0]["type"] == "run.created"
    assert events[0]["message"] == "Run created"
    assert events[0]["created_at"] is not None
    assert events[0]["event_type"] == "run.created"
    assert events[0]["trace_id"] == run["trace_id"]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert events[-1]["event_type"] == "run.completed"


def test_get_run_trace_returns_timeline_data() -> None:
    create_response = client.post("/api/runs", json={"input": "timeline please"})
    run = create_response.json()

    response = client.get(f"/api/runs/{run['id']}/trace")

    assert response.status_code == 200
    trace = response.json()
    assert trace["run_id"] == run["id"]
    assert trace["trace_id"] == run["trace_id"]
    assert [span["name"] for span in trace["spans"]] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
    assert all(span["id"].startswith("span_") for span in trace["spans"])
    assert all(span["trace_id"] == run["trace_id"] for span in trace["spans"])
    assert [event["sequence"] for event in trace["events"]] == list(range(1, 12))


def test_unknown_run_trace_returns_404() -> None:
    response = client.get("/api/runs/run_missing/trace")

    assert response.status_code == 404
