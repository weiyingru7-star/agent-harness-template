from fastapi.testclient import TestClient

from app.main import app
from core.db import session_scope
from core.db.models import RunEventRecord, RunRecord, StepRecord, TaskRecord


client = TestClient(app)


def test_run_persistence_and_api_compatibility() -> None:
    response = client.post("/api/runs", json={"input": "persist this run"})

    assert response.status_code == 201
    run = response.json()
    run_id = run["id"]

    assert run["status"] == "completed"
    assert run["trace_id"].startswith("trace_")
    assert run["task"]["input"] == "persist this run"
    assert [step["name"] for step in run["steps"]] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]

    get_response = client.get(f"/api/runs/{run_id}")
    events_response = client.get(f"/api/runs/{run_id}/events")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == run_id
    assert events_response.status_code == 200
    assert events_response.json()[0]["type"] == "run.created"
    assert events_response.json()[-1]["type"] == "run.completed"

    with session_scope() as session:
        run_record = session.get(RunRecord, run_id)
        assert run_record is not None
        assert run_record.status == "completed"
        assert run_record.trace_id == run["trace_id"]
        assert session.query(TaskRecord).count() == 1
        assert session.query(StepRecord).filter_by(run_id=run_id).count() == 4
        assert session.query(RunEventRecord).filter_by(run_id=run_id).count() == 11
        first_step = session.query(StepRecord).filter_by(run_id=run_id).first()
        assert first_step is not None
        assert first_step.trace_id == run["trace_id"]
        assert first_step.span_id is not None
        assert first_step.type == "node"
        first_event = session.query(RunEventRecord).filter_by(run_id=run_id).order_by(RunEventRecord.sequence).first()
        assert first_event is not None
        assert first_event.event_type == "run.created"
        assert first_event.trace_id == run["trace_id"]
        assert first_event.sequence == 1
