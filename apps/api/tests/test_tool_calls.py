from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_completed_run_records_tool_call() -> None:
    run = client.post("/api/runs", json={"input": "tool call path"}).json()

    response = client.get(f"/api/runs/{run['id']}/tool-calls")

    assert response.status_code == 200
    tool_calls = response.json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["run_id"] == run["id"]
    assert tool_call["step_id"]
    assert tool_call["trace_id"] == run["trace_id"]
    assert tool_call["span_id"]
    assert tool_call["tool_id"] == "mock_echo"
    assert tool_call["tool_name"] == "Mock Echo Tool"
    assert tool_call["status"] == "completed"
    assert tool_call["arguments"]["input"].startswith("Mock skill summary")
    assert tool_call["result"]["output"].startswith("Mock tool echo")
    assert tool_call["duration_ms"] is not None


def test_get_tool_call_by_id() -> None:
    run = client.post("/api/runs", json={"input": "get tool call"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    response = client.get(f"/api/tool-calls/{tool_call['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == tool_call["id"]


def test_tool_call_events_are_recorded() -> None:
    run = client.post("/api/runs", json={"input": "tool events"}).json()

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]

    assert "tool.call.started" in event_types
    assert "tool.call.completed" in event_types


def test_tool_call_is_visible_in_timeline_and_compatibility_endpoints() -> None:
    run = client.post("/api/runs", json={"input": "tool timeline"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    timeline_response = client.get(f"/api/runs/{run['id']}/timeline")
    trace_response = client.get(f"/api/runs/{run['id']}/trace")
    checkpoints_response = client.get(f"/api/runs/{run['id']}/checkpoints")

    assert timeline_response.status_code == 200
    assert trace_response.status_code == 200
    assert checkpoints_response.status_code == 200

    timeline = timeline_response.json()
    tool_items = [
        item
        for item in timeline["items"]
        if item["metadata"].get("step_name") == "tool_node"
    ]
    assert tool_items
    assert tool_items[0]["tool_call_id"] == tool_call["id"]
    assert tool_items[0]["metadata"]["tool_call_id"] == tool_call["id"]


def test_failed_run_has_no_tool_call_and_retry_still_works() -> None:
    failed_run = client.post("/api/runs", json={"input": "tool __fail__"}).json()

    tool_calls_response = client.get(f"/api/runs/{failed_run['id']}/tool-calls")
    retry_response = client.post(f"/api/runs/{failed_run['id']}/retry")

    assert tool_calls_response.status_code == 200
    assert tool_calls_response.json() == []
    assert retry_response.status_code == 201


def test_missing_tool_call_returns_404() -> None:
    response = client.get("/api/tool-calls/tool_call_missing")

    assert response.status_code == 404
