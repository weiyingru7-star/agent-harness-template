from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import Run, RunEvent, Step, Task
from core.db import session_scope
from core.db.repositories.event_repository import EventRepository
from core.db.repositories.run_repository import RunRepository
from core.db.repositories.step_repository import StepRepository
from core.db.repositories.task_repository import TaskRepository
from modules.demo_agent import run_demo_agent_state_machine


class RunStore:
    def create_run(self, task_input: str) -> Run:
        task = Task(id=self._new_id("task"), input=task_input)
        run = Run(id=self._new_id("run"), status="pending", task=task)

        with session_scope() as session:
            TaskRepository(session).create(task)
            run_repository = RunRepository(session)
            step_repository = StepRepository(session)
            event_repository = EventRepository(session)

            run_repository.create(run)
            event_repository.create(run.id, "run.created", "Run created")

            run.status = "running"
            run_repository.update(run)
            event_repository.create(run.id, "run.started", "Run started")

            state = run_demo_agent_state_machine(task_input)
            for node_trace in state.node_traces:
                step = Step(id=self._new_id("step"), name=node_trace.name, status="running")
                run.steps.append(step)
                step_repository.create(run.id, step)
                event_repository.create(
                    run_id=run.id,
                    event_type="node.started",
                    message=f"{node_trace.name} started",
                    step_id=step.id,
                )

                step.status = "completed"
                step.output = node_trace.output
                step.completed_at = self._utc_now()
                step_repository.update(step)
                event_repository.create(
                    run_id=run.id,
                    event_type="node.completed",
                    message=f"{node_trace.name} completed",
                    step_id=step.id,
                )

            run.status = "completed"
            run.output = state.final_output
            run.completed_at = self._utc_now()
            run_repository.update(run)
            event_repository.create(run.id, "run.completed", "Run completed")

        return run

    def get_run(self, run_id: str) -> Run | None:
        with session_scope() as session:
            return RunRepository(session).get(run_id)

    def get_events(self, run_id: str) -> list[RunEvent] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return EventRepository(session).list_by_run(run_id)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)


run_store = RunStore()
