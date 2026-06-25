from __future__ import annotations

from typing import Any

from app.registries.tool_result import ToolResult
from app.registries.tool_timeout import execute_with_timeout


class RetryResult:
    """Result of a retry-enabled tool execution."""

    def __init__(
        self,
        final_result: ToolResult,
        attempts: list[dict[str, Any]],
    ) -> None:
        self.final_result = final_result
        self.attempts = attempts
        self.retry_count = max(0, len(attempts) - 1)
        self.final_attempt_index = len(attempts)


def execute_with_retry(
    handler,
    base_args: dict,
    timeout_ms: int | None = None,
    max_attempts: int = 1,
    retry_on_error_types: list[str] | None = None,
) -> RetryResult:
    """Execute handler(args) with retry support.

    Each attempt calls execute_with_timeout. On failure, if the error
    type matches retry_on_error_types and attempts remain, a retry is
    performed. Returns a RetryResult with all attempt details.
    """
    effective_max = max(1, max_attempts)
    attempts: list[dict[str, Any]] = []

    for attempt_index in range(1, effective_max + 1):
        attempt_args = {**base_args, "__attempt_index__": attempt_index}
        result = execute_with_timeout(handler, attempt_args, timeout_ms)

        attempts.append(
            {
                "attempt_index": attempt_index,
                "status": result.status,
                "error_type": result.error_type,
                "error_message": result.error_message,
            }
        )

        if result.status == "completed":
            return RetryResult(final_result=result, attempts=attempts)

        if attempt_index < effective_max and _is_retryable(result, retry_on_error_types):
            continue

        return RetryResult(final_result=result, attempts=attempts)

    return RetryResult(final_result=ToolResult(status="failed", error_type="InternalError"), attempts=attempts)


def _is_retryable(result: ToolResult, retry_on: list[str] | None) -> bool:
    if retry_on is None:
        return False
    return result.error_type in retry_on
