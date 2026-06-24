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
                status=step.status,
                input=input_text,
                output=step.output,
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
            output=record.output,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )
