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


def test_invalid_tool_args_records_failed_tool_call_without_executing_tool() -> None:
    run = client.post("/api/runs", json={"input": "trigger __invalid_tool_args__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolArgsValidationError"
    assert tool_call["error_message"]
    assert tool_call["result"]["status"] == "failed"
    assert tool_call["result"]["error_type"] == "ToolArgsValidationError"
    assert tool_call["arguments"] == {"input": 123}
    assert "args_validation_errors" in tool_call["metadata"]

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "tool.call.started" in event_types
    assert "tool.call.failed" in event_types
    assert "tool.call.completed" not in event_types

    assert run["status"] == "completed"


def test_invalid_tool_args_does_not_break_normal_run_afterwards() -> None:
    invalid_run = client.post("/api/runs", json={"input": "before __invalid_tool_args__"}).json()
    normal_run = client.post("/api/runs", json={"input": "after normal"}).json()

    assert invalid_run["status"] == "completed"
    normal_tool_calls = client.get(f"/api/runs/{normal_run['id']}/tool-calls").json()
    assert normal_tool_calls[0]["status"] == "completed"


def test_tool_exception_records_failed_tool_call_without_running_tool() -> None:
    run = client.post("/api/runs", json={"input": "trigger __tool_exception__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolExecutionError"
    assert "RuntimeError" in tool_call["error_message"]
    assert tool_call["result"]["status"] == "failed"
    assert tool_call["result"]["error_type"] == "ToolExecutionError"

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "tool.call.started" in event_types
    assert "tool.call.failed" in event_types
    assert "tool.call.completed" not in event_types


def test_tool_exception_run_stays_completed() -> None:
    run = client.post("/api/runs", json={"input": "exception __tool_exception__"}).json()

    assert run["status"] == "completed"


def test_completed_tool_call_has_standard_result_structure() -> None:
    run = client.post("/api/runs", json={"input": "result structure test"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    result = tool_call["result"]
    assert result["status"] == "completed"
    assert result["output"].startswith("Mock tool echo")
    assert result["summary"].startswith("Echoed")
    assert "char_count" in result["metadata"]


def test_slow_tool_triggers_timeout() -> None:
    run = client.post("/api/runs", json={"input": "trigger __slow_tool__ timeout"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolTimeoutError"
    assert "timed out" in tool_call["error_message"]
    assert tool_call["result"]["status"] == "failed"
    assert tool_call["result"]["error_type"] == "ToolTimeoutError"
    assert tool_call["result"]["metadata"]["timeout_ms"] == 1000
    assert tool_call["duration_ms"] is not None
    assert tool_call["duration_ms"] >= 900

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "tool.call.started" in event_types
    assert "tool.call.failed" in event_types
    assert "tool.call.completed" not in event_types

    failed_events = [
        e for e in events
        if e.get("event_type") == "tool.call.failed"
        and e.get("metadata", {}).get("error_type") == "ToolTimeoutError"
    ]
    assert len(failed_events) == 1
    assert failed_events[0]["metadata"].get("timeout_ms") == 1000


def test_timeout_run_stays_completed() -> None:
    run = client.post("/api/runs", json={"input": "timeout __slow_tool__"}).json()

    assert run["status"] == "completed"


def test_timeout_is_visible_in_timeline() -> None:
    run = client.post("/api/runs", json={"input": "timeline __slow_tool__"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]
    timeline = client.get(f"/api/runs/{run['id']}/timeline").json()

    tool_items = [
        item
        for item in timeline.get("items", [])
        if item.get("metadata", {}).get("step_name") == "tool_node"
    ]
    assert tool_items
    assert tool_items[0]["tool_call_id"] == tool_call["id"]
    assert tool_items[0]["duration_ms"] is not None


def test_flaky_tool_retries_and_succeeds() -> None:
    run = client.post("/api/runs", json={"input": "retry __flaky_tool__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "completed"
    assert tool_call["metadata"]["retry_count"] == 1
    assert tool_call["metadata"]["max_attempts"] == 2
    assert tool_call["metadata"]["final_attempt_status"] == "completed"
    assert len(tool_call["metadata"]["attempts"]) == 2
    assert tool_call["metadata"]["attempts"][0]["status"] == "failed"
    assert tool_call["metadata"]["attempts"][0]["error_type"] == "ToolExecutionError"
    assert tool_call["metadata"]["attempts"][1]["status"] == "completed"
    assert tool_call["result"]["output"].startswith("Mock tool echo")


def test_flaky_tool_has_retry_scheduled_event() -> None:
    run = client.post("/api/runs", json={"input": "events __flaky_tool__"}).json()

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]

    assert "tool.call.started" in event_types
    assert "tool.call.retry_scheduled" in event_types
    assert "tool.call.completed" in event_types
    assert "tool.call.failed" not in event_types


def test_flaky_tool_run_stays_completed() -> None:
    run = client.post("/api/runs", json={"input": "completed __flaky_tool__"}).json()

    assert run["status"] == "completed"


def test_non_flaky_tool_does_not_retry() -> None:
    run = client.post("/api/runs", json={"input": "no retry here"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    assert tool_call["status"] == "completed"
    assert tool_call["metadata"].get("retry_count") is None


def test_safe_tool_executes_normally() -> None:
    run = client.post("/api/runs", json={"input": "safe tool call"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    assert tool_call["status"] == "completed"
    assert tool_call["result"]["output"].startswith("Mock tool echo")


def test_restricted_tool_is_denied() -> None:
    run = client.post("/api/runs", json={"input": "try __restricted_tool__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolPermissionDenied"
    assert tool_call["result"]["status"] == "failed"
    assert tool_call["result"]["error_type"] == "ToolPermissionDenied"

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "tool.call.started" in event_types
    assert "tool.call.failed" in event_types
    assert "tool.call.completed" not in event_types

    assert run["status"] == "completed"


def test_blocked_tool_is_denied() -> None:
    run = client.post("/api/runs", json={"input": "try __blocked_tool__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolPermissionDenied"
    assert "blocked" in tool_call["error_message"].lower()

    assert run["status"] == "completed"


def test_permission_denied_does_not_trigger_retry() -> None:
    run = client.post("/api/runs", json={"input": "perm __restricted_tool__"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    assert tool_call["status"] == "failed"
    assert tool_call["metadata"].get("retry_count") is None
    assert tool_call["metadata"].get("attempts") is None


def test_in_process_tool_executes_normally() -> None:
    run = client.post("/api/runs", json={"input": "in process tool call"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    assert tool_call["status"] == "completed"


def test_sandbox_blocked_tool_is_denied() -> None:
    run = client.post("/api/runs", json={"input": "sandbox __sandbox_blocked__"}).json()

    tool_calls = client.get(f"/api/runs/{run['id']}/tool-calls").json()
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["status"] == "failed"
    assert tool_call["error_type"] == "ToolSandboxViolation"
    assert tool_call["result"]["status"] == "failed"
    assert tool_call["result"]["error_type"] == "ToolSandboxViolation"
    assert "disabled" in tool_call["error_message"].lower()

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "tool.call.started" in event_types
    assert "tool.call.failed" in event_types
    assert "tool.call.completed" not in event_types

    assert run["status"] == "completed"


def test_sandbox_denied_does_not_trigger_retry() -> None:
    run = client.post("/api/runs", json={"input": "sbox __sandbox_blocked__"}).json()
    tool_call = client.get(f"/api/runs/{run['id']}/tool-calls").json()[0]

    assert tool_call["status"] == "failed"
    assert tool_call["metadata"].get("retry_count") is None

