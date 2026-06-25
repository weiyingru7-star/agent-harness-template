from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_get_run() -> None:
    response = client.post("/api/runs", json={"input": "hello stage two"})

    assert response.status_code == 201
    run = response.json()
    assert run["id"].startswith("run_")
    assert run["trace_id"].startswith("trace_")
    assert run["status"] == "completed"
    assert run["task"]["input"] == "hello stage two"
    assert [step["name"] for step in run["steps"]] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
    assert all(step["status"] == "completed" for step in run["steps"])
    assert run["output"] == (
        "demo_agent mock response | "
        "skill=Mock skill summary: hello stage two | "
        "tool=Mock tool echo: Mock skill summary: hello stage two"
    )

    get_response = client.get(f"/api/runs/{run['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == run["id"]


def test_create_run_with_demo_module_id() -> None:
    response = client.post(
        "/api/runs",
        json={"input": "hello module", "module_id": "demo_agent"},
    )

    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "completed"
    assert run["output"] == (
        "demo_agent mock response | "
        "skill=Mock skill summary: hello module | "
        "tool=Mock tool echo: Mock skill summary: hello module"
    )


def test_create_run_with_unknown_module_returns_400() -> None:
    response = client.post(
        "/api/runs",
        json={"input": "hello module", "module_id": "missing_module"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Module not found or disabled: missing_module"


def test_get_run_events() -> None:
    create_response = client.post("/api/runs", json={"input": "events please"})
    run_id = create_response.json()["id"]

    response = client.get(f"/api/runs/{run_id}/events")

    assert response.status_code == 200
    events = response.json()
    event_types = [event["type"] for event in events]
    assert event_types[:2] == ["run.created", "run.started"]
    assert event_types[-1] == "run.completed"
    assert event_types.count("step.started") == 4
    assert event_types.count("step.completed") == 4
    assert [event["message"] for event in events if event["type"] == "step.completed"] == [
        "input_node completed",
        "skill_node completed",
        "tool_node completed",
        "final_node completed",
    ]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert all(event["event_type"] == event["type"] for event in events)
    assert all(event["trace_id"].startswith("trace_") for event in events)


def test_unknown_run_returns_404() -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
