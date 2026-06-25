from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run import RunEvent
from core.db.models import RunEventRecord


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        run_id: str,
        event_type: str,
        message: str,
        step_id: str | None = None,
        payload: dict | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        sequence: int | None = None,
        status: str | None = None,
        started_at=None,
        ended_at=None,
        duration_ms: int | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> RunEvent:
        event = RunEvent(
            type=event_type,
            event_type=event_type,
            message=message,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            sequence=sequence,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error=error,
            metadata=metadata or {},
        )
        self.session.add(
            RunEventRecord(
                id=f"event_{uuid4().hex[:12]}",
                run_id=run_id,
                step_id=step_id,
                type=event.type,
                event_type=event.event_type,
                message=event.message,
                trace_id=event.trace_id,
                span_id=event.span_id,
                parent_span_id=event.parent_span_id,
                sequence=event.sequence,
                status=event.status,
                started_at=event.started_at,
                ended_at=event.ended_at,
                duration_ms=event.duration_ms,
                error=event.error,
                metadata_=event.metadata,
                payload=payload or {},
                created_at=event.created_at,
            )
        )
        return event

    def list_by_run(self, run_id: str) -> list[RunEvent]:
        records = self.session.scalars(
            select(RunEventRecord)
            .where(RunEventRecord.run_id == run_id)
            .order_by(RunEventRecord.sequence, RunEventRecord.created_at)
        ).all()
        return [
            RunEvent(
                type=record.type,
                event_type=record.event_type or record.type,
                message=record.message,
                trace_id=record.trace_id,
                span_id=record.span_id,
                parent_span_id=record.parent_span_id,
                sequence=record.sequence,
                status=record.status,
                started_at=record.started_at,
                ended_at=record.ended_at,
                duration_ms=record.duration_ms,
                error=record.error,
                metadata=record.metadata_ or {},
                created_at=record.created_at,
            )
            for record in records
        ]
