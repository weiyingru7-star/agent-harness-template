"""Tests for V1.8 Async Job Queue / Worker Runtime."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.job import CreateJobRequest
from app.services.job_queue import job_queue, JobQueueService
from app.services.worker_runtime import WorkerRuntime, register_handler, get_handler


client = TestClient(app)


# ── Enqueue ────────────────────────────────────────────────────────


def test_enqueue_creates_queued_job() -> None:
    resp = client.post("/api/jobs", json={"job_type": "echo", "payload": {"msg": "hello"}})
    assert resp.status_code == 201
    data = resp.json()
    assert data["job_type"] == "echo"
    assert data["status"] == "queued"
    assert data["id"].startswith("job_")


def test_get_job_returns_job() -> None:
    resp = client.post("/api/jobs", json={"job_type": "echo"})
    job_id = resp.json()["id"]
    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


def test_get_job_not_found() -> None:
    resp = client.get("/api/jobs/job_nonexistent")
    assert resp.status_code == 404


# ── List ───────────────────────────────────────────────────────────


def test_list_jobs_tenant_filter() -> None:
    client.post("/api/jobs", json={"job_type": "echo", "tenant_id": "t_a"})
    client.post("/api/jobs", json={"job_type": "echo", "tenant_id": "t_b"})
    resp = client.get("/api/jobs?tenant_id=t_a")
    assert resp.status_code == 200
    for job in resp.json():
        assert job["tenant_id"] == "t_a"


def test_list_jobs_no_tenant_returns_all() -> None:
    resp = client.get("/api/jobs")
    assert resp.status_code == 200


# ── Claim next ─────────────────────────────────────────────────────


def test_claim_next_returns_oldest_queued() -> None:
    qs = JobQueueService()
    j1 = qs.enqueue("echo", {"seq": 1})
    j2 = qs.enqueue("echo", {"seq": 2})
    claimed = qs.claim_next()
    assert claimed is not None
    assert claimed.id == j1.id
    assert claimed.status == "running"


def test_claim_next_moves_to_running() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo")
    claimed = qs.claim_next()
    assert claimed is not None
    assert claimed.attempts == 1
    assert claimed.started_at is not None
    assert claimed.status == "running"


def test_claim_next_empty_returns_none() -> None:
    qs = JobQueueService()
    # claim all queued jobs
    while qs.claim_next() is not None:
        pass
    assert qs.claim_next() is None


# ── Mark succeeded / failed ────────────────────────────────────────


def test_mark_succeeded_stores_result() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo")
    claimed = qs.claim_next()
    assert claimed is not None
    qs.mark_succeeded(claimed.id, {"output": "ok"})
    job = qs.get_job(claimed.id)
    assert job is not None
    assert job.status == "succeeded"
    assert job.result == {"output": "ok"}


def test_mark_failed_requeues_below_max() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo", max_attempts=2)
    claimed = qs.claim_next()
    assert claimed is not None
    qs.mark_failed(claimed.id, {"error": "try again"}, retryable=True)
    job = qs.get_job(claimed.id)
    assert job is not None
    assert job.status == "queued"


def test_mark_failed_final_after_max_attempts() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo", max_attempts=1)
    claimed = qs.claim_next()
    assert claimed is not None
    qs.mark_failed(claimed.id, {"error": "final"}, retryable=True)
    job = qs.get_job(claimed.id)
    assert job is not None
    assert job.status == "failed"
    assert job.finished_at is not None


# ── Cancel ─────────────────────────────────────────────────────────


def test_cancel_queued_job() -> None:
    resp = client.post("/api/jobs", json={"job_type": "echo"})
    job_id = resp.json()["id"]
    resp = client.post(f"/api/jobs/{job_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"


def test_cancel_running_returns_409() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo")
    qs.claim_next()
    resp = client.post(f"/api/jobs/{j.id}/cancel")
    assert resp.status_code == 409


def test_cancel_succeeded_returns_409() -> None:
    qs = JobQueueService()
    j = qs.enqueue("echo")
    claimed = qs.claim_next()
    assert claimed is not None
    qs.mark_succeeded(claimed.id, {})
    resp = client.post(f"/api/jobs/{j.id}/cancel")
    assert resp.status_code == 409


def test_cancel_nonexistent_returns_404() -> None:
    resp = client.post("/api/jobs/job_nonexist/cancel")
    assert resp.status_code == 404


# ── Idempotent enqueue ─────────────────────────────────────────────


def test_idempotent_enqueue_returns_existing() -> None:
    qs = JobQueueService()
    j1 = qs.enqueue("echo", tenant_id="t1", user_id="u1",
                    idempotency_key="key_001")
    j2 = qs.enqueue("echo", tenant_id="t1", user_id="u1",
                    idempotency_key="key_001")
    assert j1.id == j2.id


def test_idempotent_enqueue_different_tenant_different_job() -> None:
    qs = JobQueueService()
    j1 = qs.enqueue("echo", tenant_id="t_a", user_id="u1",
                    idempotency_key="shared_key")
    j2 = qs.enqueue("echo", tenant_id="t_b", user_id="u1",
                    idempotency_key="shared_key")
    assert j1.id != j2.id


# ── Worker runtime ─────────────────────────────────────────────────


def test_worker_echo_handler() -> None:
    qs = JobQueueService()
    qs.enqueue("echo", payload={"test": True})
    runtime = WorkerRuntime(qs)
    result = runtime.run_once()
    assert result == "succeeded"


def test_worker_missing_handler_fails_safely() -> None:
    qs = JobQueueService()
    qs.enqueue("unknown_job_type")
    runtime = WorkerRuntime(qs)
    result = runtime.run_once()
    assert "error" in result


def test_worker_custom_handler() -> None:
    qs = JobQueueService()
    register_handler("test_custom_v2", lambda p: {"custom": p.get("val")})
    qs.enqueue("test_custom_v2", payload={"val": 42})
    runtime = WorkerRuntime(qs)
    result = runtime.run_once()
    assert result == "succeeded"


def test_worker_retry_then_succeed() -> None:
    """A handler that fails first, then succeeds on retry."""
    state = {"call_count": 0}

    def flaky_handler(payload):
        state["call_count"] += 1
        if state["call_count"] == 1:
            raise RuntimeError("First attempt failed")
        return {"status": "ok"}

    register_handler("flaky", flaky_handler)
    qs = JobQueueService()
    qs.enqueue("flaky", max_attempts=2)
    runtime = WorkerRuntime(qs)

    # First run — fails, retries
    r1 = runtime.run_once()
    assert "failed" in r1

    # Second run — succeeds
    r2 = runtime.run_once()
    assert r2 == "succeeded"


# ── Legacy backward compatibility ──────────────────────────────────


def test_old_runs_unchanged() -> None:
    resp = client.post("/api/runs", json={"input": "hello"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "completed"
