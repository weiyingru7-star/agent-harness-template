from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_get_run() -> None:
    response = client.post("/api/runs", json={"input": "hello stage two"})

    assert response.status_code == 201
    run = response.json()
    assert run["id"].startswith("run_")
    assert run["status"] == "completed"
    assert run["task"]["input"] == "hello stage two"
    assert run["steps"][0]["name"] == "demo_agent"
    assert run["steps"][0]["status"] == "completed"
    assert run["output"] == "Mock response from demo_agent for: hello stage two"

    get_response = client.get(f"/api/runs/{run['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == run["id"]


def test_get_run_events() -> None:
    create_response = client.post("/api/runs", json={"input": "events please"})
    run_id = create_response.json()["id"]

    response = client.get(f"/api/runs/{run_id}/events")

    assert response.status_code == 200
    events = response.json()
    assert [event["type"] for event in events] == [
        "run.created",
        "run.started",
        "step.started",
        "step.completed",
        "run.completed",
    ]


def test_unknown_run_returns_404() -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
