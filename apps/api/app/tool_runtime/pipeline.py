"""Tool Execution Pipeline — orchestrates a single tool call end-to-end.

Extracted from RunStore._create_run (V0.7.6 refactor). Handles the full
permission → sandbox → args → execution flow with timeout/retry and
records all ToolCall + event data.

This is a structural refactor, not a new feature. All events, ToolCall
fields, sequence numbers, and metadata shapes match the previous inline
code exactly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import ToolCall
from app.registries.tool_args import ToolArgsValidator
from app.registries.tool_permission import ToolPermissionChecker
from app.registries.tool_result import ToolResult
from app.registries.tool_retry import execute_with_retry
from app.registries.tool_sandbox import ToolSandboxChecker
from app.registries.tools import ToolDefinition, get_tool, get_tool_definition


class PipelineResult:
    """Return value from ToolExecutionPipeline.execute()."""

    def __init__(self, tool_call_id: str, next_sequence: int) -> None:
        self.tool_call_id = tool_call_id
        self.next_sequence = next_sequence


class ToolExecutionPipeline:
    """Stateless pipeline that runs one tool call and records its artifacts."""

    def execute(
        self,
        *,
        node_trace,
        run_id: str,
        trace_id: str,
        span_id: str,
        step_id: str,
        sequence: int,
        event_repository,
        tool_call_repository,
    ) -> PipelineResult:
        """Run the full tool pipeline for tool_node.

        Returns PipelineResult with tool_call_id and the next sequence
        number for the caller (RunStore) to continue after this step.
        """
        tool_call_started_at = self._utc_now()
        event_repository.create(
            run_id=run_id,
            event_type="tool.call.started",
            message="mock_echo tool call started",
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            sequence=sequence,
            status="running",
            started_at=tool_call_started_at,
            metadata={
                "step_name": node_trace.name,
                "tool_id": "mock_echo",
                "tool_name": "Mock Echo Tool",
            },
        )
        sequence += 1

        tool_arguments = self._build_tool_arguments(node_trace)
        tool_definition = get_tool_definition("mock_echo")
        perm_denied = False
        effective_permission_level = (
            tool_definition.permission_level if tool_definition else "safe"
        )
        effective_allowed_contexts = (
            tool_definition.allowed_contexts if tool_definition else None
        )
        run_context = "demo"
        if node_trace.state.get("intentional_restricted_tool"):
            effective_permission_level = "restricted"
            effective_allowed_contexts = ["admin"]
        if node_trace.state.get("intentional_blocked_tool"):
            effective_permission_level = "blocked"
        if effective_permission_level != "safe":
            tmp_def = ToolDefinition(
                id="mock_echo",
                name="",
                description="",
                permission_level=effective_permission_level,
                allowed_contexts=effective_allowed_contexts,
            )
            perm_result = ToolPermissionChecker.check(tmp_def, run_context=run_context)
            if not perm_result.allowed:
                perm_denied = True

        if perm_denied:
            return self._record_permission_denied(
                node_trace=node_trace,
                run_id=run_id,
                trace_id=trace_id,
                span_id=span_id,
                step_id=step_id,
                sequence=sequence,
                event_repository=event_repository,
                tool_call_repository=tool_call_repository,
                started_at=tool_call_started_at,
                perm_result=perm_result,
                effective_permission_level=effective_permission_level,
            )

        # --- sandbox check ---
        tool_arguments = self._build_tool_arguments(node_trace)
        tool_definition = get_tool_definition("mock_echo")
        sandbox_denied = False
        effective_execution_mode = (
            tool_definition.execution_mode if tool_definition else "in_process"
        )
        if node_trace.state.get("intentional_sandbox_blocked"):
            effective_execution_mode = "disabled"
        if effective_execution_mode != "in_process":
            tmp_sbox_def = ToolDefinition(
                id="mock_echo",
                name="",
                description="",
                execution_mode=effective_execution_mode,
            )
            sbox_result = ToolSandboxChecker.check(tmp_sbox_def)
            if not sbox_result.allowed:
                sandbox_denied = True

        if sandbox_denied:
            return self._record_sandbox_denied(
                node_trace=node_trace,
                run_id=run_id,
                trace_id=trace_id,
                span_id=span_id,
                step_id=step_id,
                sequence=sequence,
                event_repository=event_repository,
                tool_call_repository=tool_call_repository,
                started_at=tool_call_started_at,
                sbox_result=sbox_result,
                effective_execution_mode=effective_execution_mode,
                tool_arguments=tool_arguments,
            )

        # --- args validation ---
        validation = ToolArgsValidator.validate(
            tool_arguments,
            tool_definition.args_schema if tool_definition else None,
        )

        if validation.valid:
            return self._execute_tool(
                node_trace=node_trace,
                run_id=run_id,
                trace_id=trace_id,
                span_id=span_id,
                step_id=step_id,
                sequence=sequence,
                event_repository=event_repository,
                tool_call_repository=tool_call_repository,
                started_at=tool_call_started_at,
                tool_arguments=tool_arguments,
                tool_definition=tool_definition,
            )
        else:
            return self._record_args_validation_failure(
                node_trace=node_trace,
                run_id=run_id,
                trace_id=trace_id,
                span_id=span_id,
                step_id=step_id,
                sequence=sequence,
                event_repository=event_repository,
                tool_call_repository=tool_call_repository,
                started_at=tool_call_started_at,
                tool_arguments=tool_arguments,
                validation=validation,
            )

    # ------------------------------------------------------------------
    # Permission denied
    # ------------------------------------------------------------------
    def _record_permission_denied(
        self,
        *,
        node_trace,
        run_id: str,
        trace_id: str,
        span_id: str,
        step_id: str,
        sequence: int,
        event_repository,
        tool_call_repository,
        started_at: datetime,
        perm_result,
        effective_permission_level: str,
    ) -> PipelineResult:
        tool_call_ended_at = self._utc_now()
        result_data = ToolResult(
            status="failed",
            error_type="ToolPermissionDenied",
            error_message=perm_result.error_message or "permission denied",
            metadata={"permission_level": effective_permission_level},
        ).model_dump()
        tool_call = ToolCall(
            id=self._new_id("tool_call"),
            run_id=run_id,
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            tool_id="mock_echo",
            tool_name="Mock Echo Tool",
            arguments={},
            result=result_data,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=self._duration_ms(started_at, tool_call_ended_at),
            error_type="ToolPermissionDenied",
            error_message=perm_result.error_message or "permission denied",
            metadata={"step_name": node_trace.name, "step_type": "node"},
        )
        tool_call_repository.create(tool_call)
        event_repository.create(
            run_id=run_id,
            event_type="tool.call.failed",
            message="mock_echo tool call failed: permission denied",
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            sequence=sequence,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=tool_call.duration_ms,
            error=perm_result.error_message or "permission denied",
            metadata={
                "step_name": node_trace.name,
                "tool_id": tool_call.tool_id,
                "tool_name": tool_call.tool_name,
                "tool_call_id": tool_call.id,
                "error_type": "ToolPermissionDenied",
                "error_message": perm_result.error_message,
                "permission_level": effective_permission_level,
                "result_status": "failed",
            },
        )
        sequence += 1
        return PipelineResult(tool_call_id=tool_call.id, next_sequence=sequence)

    # ------------------------------------------------------------------
    # Sandbox denied
    # ------------------------------------------------------------------
    def _record_sandbox_denied(
        self,
        *,
        node_trace,
        run_id: str,
        trace_id: str,
        span_id: str,
        step_id: str,
        sequence: int,
        event_repository,
        tool_call_repository,
        started_at: datetime,
        sbox_result,
        effective_execution_mode: str,
        tool_arguments: dict,
    ) -> PipelineResult:
        tool_call_ended_at = self._utc_now()
        result_data = ToolResult(
            status="failed",
            error_type="ToolSandboxViolation",
            error_message=sbox_result.error_message or "sandbox policy violation",
            metadata={"execution_mode": effective_execution_mode},
        ).model_dump()
        tool_call = ToolCall(
            id=self._new_id("tool_call"),
            run_id=run_id,
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            tool_id="mock_echo",
            tool_name="Mock Echo Tool",
            arguments=tool_arguments,
            result=result_data,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=self._duration_ms(started_at, tool_call_ended_at),
            error_type="ToolSandboxViolation",
            error_message=sbox_result.error_message or "sandbox policy violation",
            metadata={"step_name": node_trace.name, "step_type": "node"},
        )
        tool_call_repository.create(tool_call)
        event_repository.create(
            run_id=run_id,
            event_type="tool.call.failed",
            message="mock_echo tool call failed: sandbox violation",
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            sequence=sequence,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=tool_call.duration_ms,
            error=sbox_result.error_message or "sandbox policy violation",
            metadata={
                "step_name": node_trace.name,
                "tool_id": tool_call.tool_id,
                "tool_name": tool_call.tool_name,
                "tool_call_id": tool_call.id,
                "error_type": "ToolSandboxViolation",
                "error_message": sbox_result.error_message,
                "execution_mode": effective_execution_mode,
                "result_status": "failed",
            },
        )
        sequence += 1
        return PipelineResult(tool_call_id=tool_call.id, next_sequence=sequence)

    # ------------------------------------------------------------------
    # Tool execution (args valid, run with timeout/retry)
    # ------------------------------------------------------------------
    def _execute_tool(
        self,
        *,
        node_trace,
        run_id: str,
        trace_id: str,
        span_id: str,
        step_id: str,
        sequence: int,
        event_repository,
        tool_call_repository,
        started_at: datetime,
        tool_arguments: dict,
        tool_definition,
    ) -> PipelineResult:
        tool_handler = get_tool("mock_echo")
        tool_timeout_ms = tool_definition.timeout_ms if tool_definition else None
        tool_max_attempts = tool_definition.max_attempts if tool_definition else 1
        tool_retry_on = tool_definition.retry_on_error_types
        if node_trace.state.get("intentional_flaky_tool"):
            tool_max_attempts = 2
            tool_retry_on = ["ToolExecutionError"]

        retry_result = execute_with_retry(
            tool_handler,
            tool_arguments,
            timeout_ms=tool_timeout_ms,
            max_attempts=tool_max_attempts,
            retry_on_error_types=tool_retry_on,
        )

        tool_call_ended_at = self._utc_now()
        final_result = retry_result.final_result
        result_data = final_result.model_dump()
        tool_call_status = final_result.status
        tool_call_error_type = final_result.error_type
        tool_call_error_message = final_result.error_message
        result_summary = final_result.summary

        call_metadata: dict = {
            "step_name": node_trace.name,
            "step_type": "node",
        }
        if retry_result.retry_count > 0:
            call_metadata["attempts"] = retry_result.attempts
            call_metadata["max_attempts"] = tool_max_attempts
            call_metadata["retry_count"] = retry_result.retry_count
            call_metadata["final_attempt_status"] = tool_call_status

            for i, att_info in enumerate(retry_result.attempts):
                if att_info["status"] != "failed":
                    continue
                if i >= len(retry_result.attempts) - 1:
                    continue
                event_repository.create(
                    run_id=run_id,
                    event_type="tool.call.retry_scheduled",
                    message=f"retry scheduled for attempt {att_info['attempt_index']}",
                    step_id=step_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    sequence=sequence,
                    status="running",
                    metadata={
                        "attempt": att_info["attempt_index"],
                        "max_attempts": tool_max_attempts,
                        "previous_error_type": att_info["error_type"],
                        "previous_error_message": att_info["error_message"],
                        "step_name": node_trace.name,
                    },
                )
                sequence += 1

        tool_call = ToolCall(
            id=self._new_id("tool_call"),
            run_id=run_id,
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            tool_id="mock_echo",
            tool_name="Mock Echo Tool",
            arguments=tool_arguments,
            result=result_data,
            status=tool_call_status,
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=self._duration_ms(started_at, tool_call_ended_at),
            error_type=tool_call_error_type,
            error_message=tool_call_error_message,
            metadata=call_metadata,
        )
        tool_call_repository.create(tool_call)

        if tool_call_status == "completed":
            completed_metadata: dict = {
                "step_name": node_trace.name,
                "tool_id": tool_call.tool_id,
                "tool_name": tool_call.tool_name,
                "tool_call_id": tool_call.id,
                "result_status": "completed",
                "summary": result_summary,
            }
            if retry_result.retry_count > 0:
                completed_metadata["retry_count"] = retry_result.retry_count
                completed_metadata["max_attempts"] = tool_max_attempts
            event_repository.create(
                run_id=run_id,
                event_type="tool.call.completed",
                message="mock_echo tool call completed",
                step_id=step_id,
                trace_id=trace_id,
                span_id=span_id,
                sequence=sequence,
                status="completed",
                started_at=started_at,
                ended_at=tool_call_ended_at,
                duration_ms=tool_call.duration_ms,
                metadata=completed_metadata,
            )
        else:
            if tool_call_error_type == "ToolTimeoutError":
                fail_message = "mock_echo tool call failed: timeout"
            elif tool_call_error_type == "ToolExecutionError":
                fail_message = "mock_echo tool call failed: execution exception"
            else:
                fail_message = "mock_echo tool call failed"
            event_metadata: dict = {
                "step_name": node_trace.name,
                "tool_id": tool_call.tool_id,
                "tool_name": tool_call.tool_name,
                "tool_call_id": tool_call.id,
                "error_type": tool_call_error_type,
                "error_message": tool_call_error_message,
                "result_status": "failed",
            }
            if tool_call_error_type == "ToolTimeoutError" and tool_timeout_ms is not None:
                event_metadata["timeout_ms"] = tool_timeout_ms
            if retry_result.retry_count > 0:
                event_metadata["retry_count"] = retry_result.retry_count
                event_metadata["max_attempts"] = tool_max_attempts
            event_repository.create(
                run_id=run_id,
                event_type="tool.call.failed",
                message=fail_message,
                step_id=step_id,
                trace_id=trace_id,
                span_id=span_id,
                sequence=sequence,
                status="failed",
                started_at=started_at,
                ended_at=tool_call_ended_at,
                duration_ms=tool_call.duration_ms,
                error=tool_call_error_message,
                metadata=event_metadata,
            )
        sequence += 1
        return PipelineResult(tool_call_id=tool_call.id, next_sequence=sequence)

    # ------------------------------------------------------------------
    # Args validation failure
    # ------------------------------------------------------------------
    def _record_args_validation_failure(
        self,
        *,
        node_trace,
        run_id: str,
        trace_id: str,
        span_id: str,
        step_id: str,
        sequence: int,
        event_repository,
        tool_call_repository,
        started_at: datetime,
        tool_arguments: dict,
        validation,
    ) -> PipelineResult:
        tool_call_ended_at = self._utc_now()
        error = validation.error
        result_data = ToolResult(
            status="failed",
            error_type="ToolArgsValidationError",
            error_message=error.message if error else "tool args validation failed",
        ).model_dump()
        tool_call = ToolCall(
            id=self._new_id("tool_call"),
            run_id=run_id,
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            tool_id="mock_echo",
            tool_name="Mock Echo Tool",
            arguments=tool_arguments,
            result=result_data,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=self._duration_ms(started_at, tool_call_ended_at),
            error_type="ToolArgsValidationError",
            error_message=error.message if error else "tool args validation failed",
            metadata={
                "step_name": node_trace.name,
                "step_type": "node",
                "args_validation_errors": validation.details,
            },
        )
        tool_call_repository.create(tool_call)
        event_repository.create(
            run_id=run_id,
            event_type="tool.call.failed",
            message="mock_echo tool call failed: args validation",
            step_id=step_id,
            trace_id=trace_id,
            span_id=span_id,
            sequence=sequence,
            status="failed",
            started_at=started_at,
            ended_at=tool_call_ended_at,
            duration_ms=tool_call.duration_ms,
            error=tool_call.error_message,
            metadata={
                "step_name": node_trace.name,
                "tool_id": tool_call.tool_id,
                "tool_name": tool_call.tool_name,
                "tool_call_id": tool_call.id,
                "error_type": tool_call.error_type,
                "error_message": tool_call.error_message,
                "args_validation_errors": validation.details,
                "result_status": "failed",
            },
        )
        sequence += 1
        return PipelineResult(tool_call_id=tool_call.id, next_sequence=sequence)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_tool_arguments(node_trace) -> dict:
        if node_trace.state.get("intentional_invalid_args"):
            return {"input": 123}
        if node_trace.state.get("intentional_tool_exception"):
            return {"input": "__TOOL_EXCEPTION__"}
        if node_trace.state.get("intentional_slow_tool"):
            return {"input": "__SLOW_TOOL__"}
        if node_trace.state.get("intentional_flaky_tool"):
            return {"input": "__FLAKY_TOOL__"}
        return {"input": node_trace.state.get("skill_output")}

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
        return max(0, int((ended_at - started_at).total_seconds() * 1000))


# Singleton for convenience (same pattern as run_store)
tool_execution_pipeline = ToolExecutionPipeline()
