"""Worker runtime — claim next job, dispatch to handler, record result.

Template-safe sample handlers only. No business handlers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services.job_queue import JobQueueService


# ── Handler registry ──────────────────────────────────────────────

_handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}


def register_handler(job_type: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    _handlers[job_type] = handler


def get_handler(job_type: str) -> Callable[[dict[str, Any]], dict[str, Any]] | None:
    return _handlers.get(job_type)


# ── Template-safe handlers ────────────────────────────────────────

register_handler("echo", lambda p: {"echo": p})


# ── Worker runtime ────────────────────────────────────────────────


class WorkerRuntime:
    """Single-job worker — processes one queued job per call.

    Usage:
        runtime = WorkerRuntime(job_queue)
        result = runtime.run_once()  # "succeeded" | "failed: ..." | "idle"
    """

    def __init__(self, job_queue: JobQueueService) -> None:
        self.queue = job_queue

    def run_once(self) -> str:
        """Claim and execute one queued job. Returns status string."""
        job = self.queue.claim_next()
        if job is None:
            return "idle"

        handler = get_handler(job.job_type)
        if handler is None:
            self.queue.mark_failed(
                job.id,
                {"error": f"No handler registered for '{job.job_type}'"},
                retryable=False,
            )
            return f"error: unknown handler '{job.job_type}'"

        try:
            result = handler(job.payload or {})
            self.queue.mark_succeeded(job.id, result)
            return "succeeded"
        except Exception as exc:
            error = {"error_type": type(exc).__name__, "message": str(exc)}
            self.queue.mark_failed(job.id, error, retryable=True)
            return f"failed: {exc}"
