from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run import Step
from core.db.models import StepRecord


class StepRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run_id: str, step: Step, input_text: str | None = None) -> Step:
        self.session.add(
            StepRecord(
                id=step.id,
                run_id=run_id,
                name=step.name,
                type=step.type,
                status=step.status,
                trace_id=step.trace_id,
                span_id=step.span_id,
                parent_span_id=step.parent_span_id,
                input=input_text,
                output=step.output,
                started_at=step.started_at,
                ended_at=step.ended_at,
                duration_ms=step.duration_ms,
                error=step.error,
                metadata_=step.metadata,
                created_at=step.created_at,
                completed_at=step.completed_at,
            )
        )
        self.session.flush()
        return step

    def update(self, step: Step) -> Step:
        record = self.session.get(StepRecord, step.id)
        if record is not None:
            record.status = step.status
            record.output = step.output
            record.ended_at = step.ended_at
            record.duration_ms = step.duration_ms
            record.error = step.error
            record.metadata_ = step.metadata
            record.updated_at = step.completed_at
            record.completed_at = step.completed_at
        return step

    def list_by_run(self, run_id: str) -> list[Step]:
        records = self.session.scalars(
            select(StepRecord).where(StepRecord.run_id == run_id).order_by(StepRecord.created_at)
        ).all()
        return [self._to_model(record) for record in records]

    @staticmethod
    def _to_model(record: StepRecord) -> Step:
        return Step(
            id=record.id,
            name=record.name,
            status=record.status,  # type: ignore[arg-type]
            type=record.type,
            trace_id=record.trace_id,
            span_id=record.span_id,
            parent_span_id=record.parent_span_id,
            output=record.output,
            started_at=record.started_at,
            ended_at=record.ended_at,
            duration_ms=record.duration_ms,
            error=record.error,
            metadata=record.metadata_ or {},
            created_at=record.created_at,
            completed_at=record.completed_at,
        )
