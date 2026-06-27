"""Provider runtime orchestration — canonical layer.

Timeout, retry, and fallback logic for provider calls.
See docs/provider-runtime-consolidation.md.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from app.ai_runtime.providers import (
    ProviderConfigurationError,
    ProviderRequestError,
    ProviderTimeoutError,
)
from app.ai_runtime.router import ProviderRouter
from app.core.config import Settings
from app.provider_runtime.contracts import ProviderResponse


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (ProviderRequestError, ProviderTimeoutError))


def _run_with_timeout(
    handler,
    args: tuple,
    timeout_ms: int | None = None,
):
    if timeout_ms is None or timeout_ms <= 0:
        return handler(*args)

    container: dict[str, object] = {"result": None, "exception": None}

    def worker() -> None:
        try:
            container["result"] = handler(*args)
        except Exception as exc:
            container["exception"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_ms / 1000.0)

    if thread.is_alive():
        raise ProviderTimeoutError(f"Provider timed out after {timeout_ms}ms")

    if container["exception"] is not None:
        raise container["exception"]  # type: ignore

    return container["result"]


def call_provider(
    prompt: str,
    provider_name: str = "mock",
    settings: Settings | None = None,
) -> ProviderResponse:
    s = settings or Settings()
    raw_provider = ProviderRouter(s).resolve(provider_name)
    start = time.monotonic()
    result = raw_provider.generate(prompt)
    latency_ms = max(0, int((time.monotonic() - start) * 1000))
    model = getattr(raw_provider, "model", raw_provider.id)
    usage = (result.metadata or {}).get("usage", {"estimated_tokens": len(prompt.split())})
    return ProviderResponse(
        output=result.output,
        model=model,
        provider=raw_provider.id,
        latency_ms=latency_ms,
        usage=usage,
        finish_reason="stop",
        metadata=result.metadata or {},
    )


def call_provider_with_timeout_retry(
    prompt: str,
    provider_name: str = "mock",
    max_attempts: int = 1,
    timeout_ms: int | None = None,
    structured: bool = False,
    settings: Settings | None = None,
) -> ProviderResponse:
    s = settings or Settings()
    raw_provider = ProviderRouter(s).resolve(provider_name)
    attempt_records: list[dict[str, Any]] = []

    for attempt_index in range(1, max(1, max_attempts) + 1):
        try:
            start = time.monotonic()
            result = _run_with_timeout(raw_provider.generate, (prompt, structured), timeout_ms)
            latency_ms = max(0, int((time.monotonic() - start) * 1000))
            model = getattr(raw_provider, "model", raw_provider.id)
            usage = {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(result.output.split()),
                "total_tokens": len(prompt.split()) + len(result.output.split()),
            }
            response = ProviderResponse(
                output=result.output,
                model=model,
                provider=raw_provider.id,
                latency_ms=latency_ms,
                usage=usage,
                finish_reason="stop",
                metadata=result.metadata or {},
            )
            attempt_records.append({
                "attempt_index": attempt_index,
                "status": "completed",
                "latency_ms": latency_ms,
            })
            if len(attempt_records) > 1:
                response.metadata["attempts"] = attempt_records
                response.metadata["max_attempts"] = max_attempts
                response.metadata["retry_count"] = len(attempt_records) - 1
                response.metadata["retried"] = True
                response.metadata["final_attempt_status"] = "completed"
            return response
        except (ProviderRequestError, ProviderTimeoutError) as exc:
            attempt_records.append({
                "attempt_index": attempt_index,
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "timeout_ms_configured": timeout_ms,
            })
            if attempt_index < max_attempts and _is_retryable(exc):
                continue
            raise

    # Should not reach here
    raise ProviderRequestError("retry exhausted but no result")


def call_provider_with_fallback(
    prompt: str,
    primary: str = "mock",
    fallback: str = "mock",
    settings: Settings | None = None,
) -> ProviderResponse:
    try:
        return call_provider(prompt, primary, settings)
    except Exception as exc:
        meta: dict[str, Any] = {
            "fallback_used": True,
            "fallback_from": primary,
            "fallback_to": fallback,
            "fallback_reason": f"{type(exc).__name__}: {exc}",
            "primary_error_type": type(exc).__name__,
        }
        response = call_provider(prompt, fallback, settings)
        response.metadata.update(meta)
        return response
