from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run import Run, Task
from core.db.models import RunRecord, TaskRecord
from core.db.repositories.step_repository import StepRepository


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run: Run, module_id: str | None = "demo_agent", agent_id: str | None = None) -> Run:
        self.session.add(
            RunRecord(
                id=run.id,
                trace_id=run.trace_id,
                task_id=run.task.id,
                module_id=module_id,
                agent_id=agent_id,
                input=run.task.input,
                output=run.output,
                status=run.status,
                created_at=run.created_at,
                completed_at=run.completed_at,
            )
        )
        self.session.flush()
        return run

    def update(self, run: Run) -> Run:
        record = self.session.get(RunRecord, run.id)
        if record is not None:
            record.status = run.status
            record.output = run.output
            record.trace_id = run.trace_id
            record.updated_at = run.completed_at
            record.completed_at = run.completed_at
        return run

    def exists(self, run_id: str) -> bool:
        return self.session.get(RunRecord, run_id) is not None

    def get(self, run_id: str) -> Run | None:
        record = self.session.get(RunRecord, run_id)
        if record is None:
            return None

        task_record = self.session.get(TaskRecord, record.task_id) if record.task_id else None
        task = Task(
            id=task_record.id if task_record else record.task_id or f"task_{record.id}",
            input=task_record.input if task_record else record.input,
            created_at=task_record.created_at if task_record else record.created_at,
        )
        return Run(
            id=record.id,
            trace_id=record.trace_id,
            status=record.status,  # type: ignore[arg-type]
            task=task,
            steps=StepRepository(self.session).list_by_run(record.id),
            output=record.output,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )

    def list_recent(self, limit: int = 20) -> list[Run]:
        records = self.session.scalars(
            select(RunRecord).order_by(RunRecord.created_at.desc()).limit(limit)
        ).all()
        return [run for record in records if (run := self.get(record.id)) is not None]
