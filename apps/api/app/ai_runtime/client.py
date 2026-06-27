"""LLM client — legacy compatibility layer.

Prefer call_provider / call_provider_with_timeout_retry from
app.provider_runtime for new provider features.
See docs/provider-runtime-consolidation.md.
"""

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.ai_runtime.providers import LLMProvider
from app.ai_runtime.structured_output import parse_structured_output_or_raise


class LLMResponse(BaseModel):
    provider: str
    output: str
    structured_output: dict[str, Any] | None = None
    model: str = ""
    latency_ms: int | None = None
    usage: dict = Field(default_factory=dict)
    finish_reason: str | None = None
    metadata: dict = Field(default_factory=dict)


class ProviderStreamEvent(BaseModel):
    event_type: str  # "stream_start" | "stream_delta" | "stream_end" | "stream_error"
    delta: str | None = None
    index: int = 0
    provider: str = ""
    model: str = ""
    metadata: dict = Field(default_factory=dict)


@dataclass(frozen=True)
class LLMClient:
    provider: LLMProvider

    def generate(self, prompt: str, structured: bool = False) -> LLMResponse:
        start = time.monotonic()
        if structured:
            result = self.provider.generate_json(prompt=prompt)
            parsed_output = parse_structured_output_or_raise(result.output)
        else:
            result = self.provider.generate_text(prompt=prompt)
            parsed_output = None
        latency_ms = int((time.monotonic() - start) * 1000)

        prompt_tokens = len(prompt.split())
        completion_tokens = len(result.output.split())

        return LLMResponse(
            provider=self.provider.id,
            output=result.output,
            structured_output=parsed_output,
            model=getattr(self.provider, "model", self.provider.id),
            latency_ms=latency_ms,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason="stop",
            metadata={
                "provider_runtime_version": "v0.5.1",
                "contract": "ProviderResponse",
                "mock": self.provider.id == "mock",
            },
        )

    def generate_stream(self, prompt: str) -> Iterator[ProviderStreamEvent]:
        model = getattr(self.provider, "model", self.provider.id)
        yield ProviderStreamEvent(
            event_type="stream_start", index=0,
            provider=self.provider.id, model=model,
        )

        index = 1
        try:
            for delta in self.provider.stream_text(prompt):
                yield ProviderStreamEvent(
                    event_type="stream_delta", delta=delta, index=index,
                    provider=self.provider.id, model=model,
                )
                index += 1
            yield ProviderStreamEvent(
                event_type="stream_end", index=index,
                provider=self.provider.id, model=model,
            )
        except Exception as exc:
            yield ProviderStreamEvent(
                event_type="stream_error", delta=str(exc), index=index,
                provider=self.provider.id, model=model,
            )
