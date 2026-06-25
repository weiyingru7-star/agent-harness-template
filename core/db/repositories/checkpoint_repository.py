from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run import Checkpoint
from core.db.models import CheckpointRecord


class CheckpointRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, checkpoint: Checkpoint) -> Checkpoint:
        self.session.add(
            CheckpointRecord(
                id=checkpoint.id,
                run_id=checkpoint.run_id,
                step_id=checkpoint.step_id,
                trace_id=checkpoint.trace_id,
                span_id=checkpoint.span_id,
                checkpoint_index=checkpoint.checkpoint_index,
                state=checkpoint.state,
                metadata_=checkpoint.metadata,
                created_at=checkpoint.created_at,
            )
        )
        self.session.flush()
        return checkpoint

    def get(self, checkpoint_id: str) -> Checkpoint | None:
        record = self.session.get(CheckpointRecord, checkpoint_id)
        if record is None:
            return None
        return self._to_model(record)

    def list_by_run(self, run_id: str) -> list[Checkpoint]:
        records = self.session.scalars(
            select(CheckpointRecord)
            .where(CheckpointRecord.run_id == run_id)
            .order_by(CheckpointRecord.checkpoint_index)
        ).all()
        return [self._to_model(record) for record in records]

    @staticmethod
    def _to_model(record: CheckpointRecord) -> Checkpoint:
        return Checkpoint(
            id=record.id,
            run_id=record.run_id,
            step_id=record.step_id,
            trace_id=record.trace_id,
            span_id=record.span_id,
            checkpoint_index=record.checkpoint_index,
            state=record.state or {},
            metadata=record.metadata_ or {},
            created_at=record.created_at,
        )
