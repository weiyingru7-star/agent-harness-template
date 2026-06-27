from __future__ import annotations

from core.db import session_scope
from core.db.repositories.job_repository import JobRepository
from app.models.job import Job


class JobQueueService:
    """Job queue — enqueue, query, claim, complete, cancel.

    DB-backed (SQLAlchemy + SQLite). Single-process MVP.
    """

    def enqueue(
        self,
        job_type: str,
        payload: dict | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        max_attempts: int = 1,
    ) -> Job:
        """Create a job. Idempotent: same scoped key returns existing job."""
        if idempotency_key:
            existing = self._find_by_scope(
                tenant_id, user_id, job_type, idempotency_key,
            )
            if existing is not None:
                return existing

        with session_scope() as session:
            repo = JobRepository(session)
            return repo.create(
                job_type=job_type,
                payload=payload,
                tenant_id=tenant_id,
                user_id=user_id,
                request_id=request_id,
                idempotency_key=idempotency_key,
                max_attempts=max_attempts,
            )

    def _find_by_scope(
        self, tenant_id, user_id, job_type, idempotency_key,
    ) -> Job | None:
        with session_scope() as session:
            return JobRepository(session).find_by_idempotency_scope(
                tenant_id, user_id, job_type, idempotency_key,
            )

    def get_job(self, job_id: str) -> Job | None:
        with session_scope() as session:
            return JobRepository(session).get(job_id)

    def list_jobs(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: str | None = None,
    ) -> list[Job]:
        with session_scope() as session:
            return JobRepository(session).list(
                tenant_id=tenant_id, user_id=user_id, status=status,
            )

    def claim_next(self) -> Job | None:
        with session_scope() as session:
            return JobRepository(session).claim_next()

    def mark_succeeded(self, job_id: str, result: dict | None = None) -> Job | None:
        with session_scope() as session:
            return JobRepository(session).update_status(
                job_id, "succeeded", result=result, finished=True,
            )

    def mark_failed(self, job_id: str, error: dict | None = None,
                    retryable: bool = True) -> Job | None:
        with session_scope() as session:
            repo = JobRepository(session)
            job = repo.get(job_id)
            if job is None:
                return None
            if retryable and (job.attempts < job.max_attempts):
                return repo.update_requeue(job_id, error=error or {})
            return repo.update_status(
                job_id, "failed", error=error, finished=True,
            )

    def cancel(self, job_id: str) -> Job | None:
        with session_scope() as session:
            repo = JobRepository(session)
            job = repo.get(job_id)
            if job is None:
                return None
            if job.status == "queued":
                return repo.update_status(job_id, "canceled")
            return None  # Not cancellable


job_queue = JobQueueService()
