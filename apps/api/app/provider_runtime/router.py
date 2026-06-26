from __future__ import annotations

import time
from typing import Any

from app.ai_runtime.router import ProviderRouter
from app.core.config import Settings
from app.provider_runtime.contracts import ProviderResponse


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
