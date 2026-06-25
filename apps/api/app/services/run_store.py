from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import Run, RunEvent, RunTrace, Step, Task, TraceSpan
from core.db import session_scope
from core.db.repositories.event_repository import EventRepository
from core.db.repositories.run_repository import RunRepository
from core.db.repositories.step_repository import StepRepository
from core.db.repositories.task_repository import TaskRepository
from app.registries.modules import execute_module


class RunStore:
    def create_run(self, task_input: str, module_id: str | None = None) -> Run:
        selected_module_id = module_id or "demo_agent"
        task = Task(id=self._new_id("task"), input=task_input)
        trace_id = self._new_id("trace")
        run = Run(id=self._new_id("run"), trace_id=trace_id, status="pending", task=task)
        sequence = 1

        with session_scope() as session:
            TaskRepository(session).create(task)
            run_repository = RunRepository(session)
            step_repository = StepRepository(session)
            event_repository = EventRepository(session)

            run_repository.create(run)
            event_repository.create(
                run.id,
                "run.created",
                "Run created",
                trace_id=trace_id,
                sequence=sequence,
                status="pending",
                metadata={"module_id": selected_module_id},
            )
            sequence += 1

            run.status = "running"
            run_repository.update(run)
            event_repository.create(
                run.id,
                "run.started",
                "Run started",
                trace_id=trace_id,
                sequence=sequence,
                status="running",
                metadata={"module_id": selected_module_id},
            )
            sequence += 1

            result = execute_module(selected_module_id, task_input, run.id)
            for node_trace in result.steps:
                step_started_at = self._utc_now()
                span_id = self._new_id("span")
                step = Step(
                    id=self._new_id("step"),
                    name=node_trace.name,
                    status="running",
                    type="node",
                    trace_id=trace_id,
                    span_id=span_id,
                    started_at=step_started_at,
                    metadata={"module_id": selected_module_id},
                )
                run.steps.append(step)
                step_repository.create(run.id, step)
                event_repository.create(
                    run_id=run.id,
                    event_type="step.started",
                    message=f"{node_trace.name} started",
                    step_id=step.id,
                    trace_id=trace_id,
                    span_id=span_id,
                    sequence=sequence,
                    status="running",
                    started_at=step_started_at,
                    metadata={"step_name": node_trace.name, "step_type": step.type},
                )
                sequence += 1

                step_ended_at = self._utc_now()
                step.status = "completed"
                step.output = node_trace.output
                step.ended_at = step_ended_at
                step.duration_ms = self._duration_ms(step_started_at, step_ended_at)
                step.completed_at = step_ended_at
                step_repository.update(step)
                event_repository.create(
                    run_id=run.id,
                    event_type="step.completed",
                    message=f"{node_trace.name} completed",
                    step_id=step.id,
                    trace_id=trace_id,
                    span_id=span_id,
                    sequence=sequence,
                    status="completed",
                    started_at=step_started_at,
                    ended_at=step_ended_at,
                    duration_ms=step.duration_ms,
                    metadata={"step_name": node_trace.name, "step_type": step.type},
                )
                sequence += 1

            run.status = "completed"
            run.output = result.output
            run.completed_at = self._utc_now()
            run_repository.update(run)
            event_repository.create(
                run.id,
                "run.completed",
                "Run completed",
                trace_id=trace_id,
                sequence=sequence,
                status="completed",
                ended_at=run.completed_at,
                metadata={"module_id": selected_module_id},
            )

        return run

    def get_run(self, run_id: str) -> Run | None:
        with session_scope() as session:
            return RunRepository(session).get(run_id)

    def get_events(self, run_id: str) -> list[RunEvent] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return EventRepository(session).list_by_run(run_id)

    def get_trace(self, run_id: str) -> RunTrace | None:
        with session_scope() as session:
            run = RunRepository(session).get(run_id)
            if run is None:
                return None

            events = EventRepository(session).list_by_run(run_id)
            trace_id = run.trace_id or next(
                (event.trace_id for event in events if event.trace_id),
                None,
            )
            spans = [
                TraceSpan(
                    id=step.span_id or step.id,
                    trace_id=step.trace_id or trace_id,
                    run_id=run.id,
                    step_id=step.id,
                    parent_span_id=step.parent_span_id,
                    name=step.name,
                    type=step.type,
                    status=step.status,
                    started_at=step.started_at,
                    ended_at=step.ended_at,
                    duration_ms=step.duration_ms,
                    error=step.error,
                    metadata=step.metadata,
                )
                for step in run.steps
            ]
            return RunTrace(run_id=run.id, trace_id=trace_id, spans=spans, events=events)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
        return max(0, int((ended_at - started_at).total_seconds() * 1000))


run_store = RunStore()
