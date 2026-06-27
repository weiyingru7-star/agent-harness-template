from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from core.db.models import JobRecord


def utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _new_id() -> str:
        return f"job_{uuid4().hex[:12]}"

    @staticmethod
    def _from_record(rec: JobRecord) -> Job:
        return Job(
            id=rec.id,
            job_type=rec.job_type,
            status=rec.status,
            tenant_id=rec.tenant_id,
            user_id=rec.user_id,
            request_id=rec.request_id,
            idempotency_key=rec.idempotency_key,
            payload=rec.payload or {},
            result=rec.result,
            error=rec.error,
            attempts=rec.attempts,
            max_attempts=rec.max_attempts,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            started_at=rec.started_at,
            finished_at=rec.finished_at,
        )

    def create(
        self,
        job_type: str,
        payload: dict | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        max_attempts: int = 1,
    ) -> Job:
        now = utc_now()
        record = JobRecord(
            id=self._new_id(),
            job_type=job_type,
            status="queued",
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            payload=payload or {},
            attempts=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self.session.flush()
        return self._from_record(record)

    def get(self, job_id: str) -> Job | None:
        record = self.session.get(JobRecord, job_id)
        if record is None:
            return None
        return self._from_record(record)

    def list(self, tenant_id: str | None = None,
             user_id: str | None = None,
             status: str | None = None) -> list[Job]:
        stmt = select(JobRecord)
        if tenant_id:
            stmt = stmt.where(JobRecord.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(JobRecord.user_id == user_id)
        if status:
            stmt = stmt.where(JobRecord.status == status)
        stmt = stmt.order_by(JobRecord.created_at.desc())
        return [self._from_record(r) for r in self.session.execute(stmt).scalars().all()]

    def claim_next(self) -> Job | None:
        """Claim the oldest queued job for execution.

        SQLite MVP — SELECT + UPDATE. Not for distributed workers.
        """
        stmt = (
            select(JobRecord)
            .where(JobRecord.status == "queued")
            .where(JobRecord.attempts < JobRecord.max_attempts)
            .order_by(JobRecord.created_at.asc())
            .limit(1)
        )
        record = self.session.execute(stmt).scalar_one_or_none()
        if record is None:
            return None
        now = utc_now()
        record.status = "running"
        record.attempts = (record.attempts or 0) + 1
        record.started_at = now
        record.updated_at = now
        self.session.flush()
        return self._from_record(record)

    def update_status(self, job_id: str, status: str,
                      result: dict | None = None,
                      error: dict | None = None,
                      finished: bool = False) -> Job | None:
        record = self.session.get(JobRecord, job_id)
        if record is None:
            return None
        now = utc_now()
        record.status = status
        record.updated_at = now
        if result is not None:
            record.result = result
        if error is not None:
            record.error = error
        if finished:
            record.finished_at = now
        self.session.flush()
        return self._from_record(record)

    def update_requeue(self, job_id: str, error: dict) -> Job | None:
        """Re-queue a failed job for retry."""
        record = self.session.get(JobRecord, job_id)
        if record is None:
            return None
        now = utc_now()
        record.status = "queued"
        record.error = error
        record.updated_at = now
        self.session.flush()
        return self._from_record(record)

    def find_by_idempotency_scope(
        self, tenant_id: str | None, user_id: str | None,
        job_type: str, idempotency_key: str,
    ) -> Job | None:
        stmt = (
            select(JobRecord)
            .where(JobRecord.tenant_id == tenant_id)
            .where(JobRecord.user_id == user_id)
            .where(JobRecord.job_type == job_type)
            .where(JobRecord.idempotency_key == idempotency_key)
            .limit(1)
        )
        record = self.session.execute(stmt).scalar_one_or_none()
        return self._from_record(record) if record else None
