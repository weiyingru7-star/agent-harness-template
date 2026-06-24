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
    ) -> RunEvent:
        event = RunEvent(type=event_type, message=message)
        self.session.add(
            RunEventRecord(
                id=f"event_{uuid4().hex[:12]}",
                run_id=run_id,
                step_id=step_id,
                type=event.type,
                message=event.message,
                payload=payload or {},
                created_at=event.created_at,
            )
        )
        return event

    def list_by_run(self, run_id: str) -> list[RunEvent]:
        records = self.session.scalars(
            select(RunEventRecord)
            .where(RunEventRecord.run_id == run_id)
            .order_by(RunEventRecord.created_at)
        ).all()
        return [
            RunEvent(
                type=record.type,
                message=record.message,
                created_at=record.created_at,
            )
            for record in records
        ]
