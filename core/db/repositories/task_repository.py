from sqlalchemy.orm import Session

from app.models.run import Task
from core.db.models import TaskRecord


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, task: Task, status: str = "pending") -> Task:
        self.session.add(
            TaskRecord(
                id=task.id,
                input=task.input,
                status=status,
                created_at=task.created_at,
            )
        )
        self.session.flush()
        return task

    def get(self, task_id: str) -> Task | None:
        record = self.session.get(TaskRecord, task_id)
        if record is None:
            return None
        return Task(
            id=record.id,
            input=record.input,
            created_at=record.created_at,
        )
