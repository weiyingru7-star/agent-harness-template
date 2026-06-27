from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import (
    Checkpoint,
    Run,
    RunEvent,
    RunTimeline,
    RunTrace,
    Step,
    Task,
    TimelineItem,
    ToolCall,
    TraceSpan,
)
from core.db import session_scope
from core.db.repositories.checkpoint_repository import CheckpointRepository
from core.db.repositories.event_repository import EventRepository
from core.db.repositories.run_repository import RunRepository
from core.db.repositories.step_repository import StepRepository
from core.db.repositories.task_repository import TaskRepository
from core.db.repositories.tool_call_repository import ToolCallRepository
from app.registries.modules import execute_module
from app.tool_runtime import ToolExecutionPipeline


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
            tool_call_repository = ToolCallRepository(session)

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

            # ── Input guardrail dry-run hook (V0.8.6) ────────────────
            from app.policies.dry_run_hooks import run_input_guardrail
            sequence = run_input_guardrail(
                task_input=task_input,
                run_id=run.id,
                run_metadata=run_metadata,
                trace_id=trace_id,
                sequence=sequence,
                event_repository=event_repository,
                policies=[],      # No policies loaded yet — no-op by default
                guardrails=[],
            )
            # ── End input guardrail hook ─────────────────────────────

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

                tool_call_id = None
                if node_trace.name == "tool_node":
                    pipeline_result = ToolExecutionPipeline().execute(
                        node_trace=node_trace,
                        run_id=run.id,
                        trace_id=trace_id,
                        span_id=span_id,
                        step_id=step.id,
                        sequence=sequence,
                        event_repository=event_repository,
                        tool_call_repository=tool_call_repository,
                    )
                    tool_call_id = pipeline_result.tool_call_id
                    sequence = pipeline_result.next_sequence

                step.status = "completed"
                step.output = node_trace.output
                step.ended_at = step_ended_at
                step.duration_ms = self._duration_ms(step_started_at, step_ended_at)
                step.completed_at = step_ended_at
                if tool_call_id is not None:
                    step.metadata = {
                        **step.metadata,
                        "step_name": node_trace.name,
                        "step_type": step.type,
                        "tool_call_id": tool_call_id,
                    }
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
                    metadata={
                        "step_name": node_trace.name,
                        "step_type": step.type,
                        **({"tool_call_id": tool_call_id} if tool_call_id else {}),
                    },
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
                        metadata={
                            "step_name": node_trace.name,
                            "step_type": step.type,
                            **({"tool_call_id": tool_call_id} if tool_call_id else {}),
                        },
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

    def get_timeline(self, run_id: str) -> RunTimeline | None:
        with session_scope() as session:
            run = RunRepository(session).get(run_id)
            if run is None:
                return None

            events = EventRepository(session).list_by_run(run_id)
            checkpoints = CheckpointRepository(session).list_by_run(run_id)
            tool_calls = ToolCallRepository(session).list_by_run(run_id)
            checkpoint_by_step_id = {checkpoint.step_id: checkpoint for checkpoint in checkpoints}
            tool_call_by_step_id = {tool_call.step_id: tool_call for tool_call in tool_calls}
            terminal_events_by_span_id = {}
            for event in events:
                if event.span_id and event.event_type in {"step.completed", "step.failed"}:
                    terminal_events_by_span_id[event.span_id] = event

            items = [
                self._build_step_timeline_item(
                    step,
                    checkpoint_by_step_id.get(step.id),
                    tool_call_by_step_id.get(step.id),
                    terminal_events_by_span_id.get(step.span_id or ""),
                )
                for step in run.steps
            ]

            for event in events:
                if event.event_type in {"run.retry_started", "run.retry_completed"}:
                    items.append(
                        TimelineItem(
                            type="retry",
                            label=event.message,
                            status=event.status,
                            sequence=event.sequence,
                            started_at=event.started_at,
                            ended_at=event.ended_at,
                            duration_ms=event.duration_ms,
                            error_message=event.error,
                            metadata=event.metadata,
                        )
                    )

            items.sort(key=lambda item: (item.sequence is None, item.sequence or 0, item.label))
            return RunTimeline(
                run_id=run.id,
                trace_id=run.trace_id,
                status=run.status,
                started_at=run.created_at,
                ended_at=run.completed_at,
                duration_ms=self._duration_ms(run.created_at, run.completed_at)
                if run.completed_at
                else None,
                items=items,
            )

    def get_checkpoints(self, run_id: str) -> list[Checkpoint] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return CheckpointRepository(session).list_by_run(run_id)

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        with session_scope() as session:
            return CheckpointRepository(session).get(checkpoint_id)

    def get_tool_calls(self, run_id: str) -> list[ToolCall] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return ToolCallRepository(session).list_by_run(run_id)

    def get_tool_call(self, tool_call_id: str) -> ToolCall | None:
        with session_scope() as session:
            return ToolCallRepository(session).get(tool_call_id)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
        return max(0, int((ended_at - started_at).total_seconds() * 1000))

    @staticmethod
    def _build_step_timeline_item(
        step: Step,
        checkpoint: Checkpoint | None,
        tool_call: ToolCall | None,
        terminal_event: RunEvent | None,
    ) -> TimelineItem:
        metadata = dict(step.metadata)
        if terminal_event is not None:
            metadata.update(terminal_event.metadata)
        if tool_call is not None:
            metadata["tool_call_id"] = tool_call.id
        return TimelineItem(
            type="step",
            label=f"{step.name} {step.status}",
            status=step.status,
            step_id=step.id,
            span_id=step.span_id,
            tool_call_id=tool_call.id if tool_call else None,
            checkpoint_id=checkpoint.id if checkpoint else None,
            checkpoint_index=checkpoint.checkpoint_index if checkpoint else None,
            sequence=terminal_event.sequence if terminal_event else None,
            started_at=step.started_at,
            ended_at=step.ended_at,
            duration_ms=step.duration_ms,
            error_type=step.error_type,
            error_message=step.error_message or step.error,
            metadata=metadata,
        )


run_store = RunStore()
