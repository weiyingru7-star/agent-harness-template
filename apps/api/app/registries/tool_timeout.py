from __future__ import annotations

import threading

from app.registries.tool_result import ToolResult


def execute_with_timeout(
    handler,
    args: dict,
    timeout_ms: int | None = None,
) -> ToolResult:
    """Execute handler(args), returning a ToolResult.

    If timeout_ms is set and the handler takes longer than timeout_ms,
    a failed ToolResult with ToolTimeoutError is returned instead.

    This function never raises — timeouts and handler exceptions are
    both captured and returned as failed ToolResults.
    """
    if timeout_ms is None or timeout_ms <= 0:
        return _run_handler(handler, args)

    container: dict = {"result": None, "exception": None}

    def worker() -> None:
        try:
            container["result"] = handler(args)
        except Exception as exc:
            container["exception"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_ms / 1000.0)

    if thread.is_alive():
        return ToolResult(
            status="failed",
            error_type="ToolTimeoutError",
            error_message=f"Tool timed out after {timeout_ms}ms",
            metadata={"timeout_ms": timeout_ms},
        )

    if container["exception"] is not None:
        exc = container["exception"]
        return ToolResult(
            status="failed",
            error_type="ToolExecutionError",
            error_message=f"{type(exc).__name__}: {exc}",
        )

    result = container["result"]
    if isinstance(result, ToolResult):
        return result
    return ToolResult(status="completed", output=str(result))


def _run_handler(handler, args: dict) -> ToolResult:
    try:
        result = handler(args)
        if isinstance(result, ToolResult):
            return result
        return ToolResult(status="completed", output=str(result))
    except Exception as exc:
        return ToolResult(
            status="failed",
            error_type="ToolExecutionError",
            error_message=f"{type(exc).__name__}: {exc}",
        )
