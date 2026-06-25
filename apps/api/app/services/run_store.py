from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import Checkpoint, Run, RunEvent, RunTrace, Step, Task, TraceSpan
from core.db import session_scope
from core.db.repositories.checkpoint_repository import CheckpointRepository
from core.db.repositories.event_repository import EventRepository
from core.db.repositories.run_repository import RunRepository
from core.db.repositories.step_repository import StepRepository
from core.db.repositories.task_repository import TaskRepository
from app.registries.modules import execute_module


class RunStore:
    def create_run(self, task_input: str, module_id: str | None = None) -> Run:
        return self._create_run(task_input=task_input, module_id=module_id)

    def retry_run(self, run_id: str) -> Run | None:
        original_run = self.get_run(run_id)
        if original_run is None:
            return None
        if original_run.status != "failed":
            raise ValueError("Only failed runs can be retried")
        return self._create_run(
            task_input=original_run.task.input,
            module_id=original_run.metadata.get("module_id") if original_run.metadata else None,
            attempt=original_run.metadata.get("attempt", 1) + 1 if original_run.metadata else 2,
            retry_of_run_id=run_id,
        )

    def _create_run(
        self,
        task_input: str,
        module_id: str | None = None,
        attempt: int = 1,
        retry_of_run_id: str | None = None,
    ) -> Run:
        selected_module_id = module_id or "demo_agent"
        task = Task(id=self._new_id("task"), input=task_input)
        trace_id = self._new_id("trace")
        run_metadata = {"module_id": selected_module_id, "attempt": attempt}
        if retry_of_run_id is not None:
            run_metadata["retry_of_run_id"] = retry_of_run_id
        run = Run(
            id=self._new_id("run"),
            trace_id=trace_id,
            status="pending",
            task=task,
            metadata=run_metadata,
        )
        sequence = 1

        with session_scope() as session:
            TaskRepository(session).create(task)
            run_repository = RunRepository(session)
            step_repository = StepRepository(session)
            event_repository = EventRepository(session)
            checkpoint_repository = CheckpointRepository(session)

            run_repository.create(run)
            event_repository.create(
                run.id,
                "run.created",
                "Run created",
                trace_id=trace_id,
                sequence=sequence,
                status="pending",
                metadata=run_metadata,
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
                metadata=run_metadata,
            )
            sequence += 1
            if retry_of_run_id is not None:
                event_repository.create(
                    run.id,
                    "run.retry_started",
                    "Run retry started",
                    trace_id=trace_id,
                    sequence=sequence,
                    status="running",
                    metadata=run_metadata,
                )
                sequence += 1

            result = execute_module(selected_module_id, task_input, run.id)
            checkpoint_index = 1
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
                    attempt=attempt,
                    max_attempts=max(1, attempt),
                    metadata=run_metadata,
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
                if node_trace.status == "failed":
                    step.status = "failed"
                    step.output = node_trace.output
                    step.ended_at = step_ended_at
                    step.duration_ms = self._duration_ms(step_started_at, step_ended_at)
                    step.completed_at = step_ended_at
                    step.failed_at = step_ended_at
                    step.error_type = node_trace.error_type or "AgentStepFailed"
                    step.error_message = node_trace.error_message or "Agent step failed"
                    step.error = step.error_message
                    step.metadata = {
                        **run_metadata,
                        "step_name": node_trace.name,
                        "step_type": step.type,
                    }
                    step_repository.update(step)
                    event_repository.create(
                        run_id=run.id,
                        event_type="step.failed",
                        message=f"{node_trace.name} failed",
                        step_id=step.id,
                        trace_id=trace_id,
                        span_id=span_id,
                        sequence=sequence,
                        status="failed",
                        started_at=step_started_at,
                        ended_at=step_ended_at,
                        duration_ms=step.duration_ms,
                        error=step.error_message,
                        metadata={
                            "step_name": node_trace.name,
                            "step_type": step.type,
                            "error_type": step.error_type,
                            "error_message": step.error_message,
                        },
                    )
                    sequence += 1

                    run.status = "failed"
                    run.error_type = step.error_type
                    run.error_message = step.error_message
                    run.failed_at = step_ended_at
                    run.completed_at = step_ended_at
                    run.output = None
                    run_repository.update(run)
                    event_repository.create(
                        run.id,
                        "run.failed",
                        "Run failed",
                        trace_id=trace_id,
                        sequence=sequence,
                        status="failed",
                        ended_at=step_ended_at,
                        error=step.error_message,
                        metadata={
                            **run_metadata,
                            "error_type": step.error_type,
                            "error_message": step.error_message,
                        },
                    )
                    return run

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
                checkpoint_repository.create(
                    Checkpoint(
                        id=self._new_id("checkpoint"),
                        run_id=run.id,
                        step_id=step.id,
                        trace_id=trace_id,
                        span_id=span_id,
                        checkpoint_index=checkpoint_index,
                        state=node_trace.state,
                        metadata={"step_name": node_trace.name, "step_type": step.type},
                    )
                )
                checkpoint_index += 1
                sequence += 1

            run.status = "completed"
            run.output = result.output
            run.completed_at = self._utc_now()
            run_repository.update(run)
            if retry_of_run_id is not None:
                event_repository.create(
                    run.id,
                    "run.retry_completed",
                    "Run retry completed",
                    trace_id=trace_id,
                    sequence=sequence,
                    status="completed",
                    ended_at=run.completed_at,
                    metadata=run_metadata,
                )
                sequence += 1
            event_repository.create(
                run.id,
                "run.completed",
                "Run completed",
                trace_id=trace_id,
                sequence=sequence,
                status="completed",
                ended_at=run.completed_at,
                metadata=run_metadata,
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

    def get_checkpoints(self, run_id: str) -> list[Checkpoint] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return CheckpointRepository(session).list_by_run(run_id)

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        with session_scope() as session:
            return CheckpointRepository(session).get(checkpoint_id)

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
