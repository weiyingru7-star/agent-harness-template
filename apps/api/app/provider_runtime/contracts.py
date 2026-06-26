from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderRequest(BaseModel):
    input: str
    model: str = Field(default="mock")
    messages: list[dict] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict = Field(default_factory=dict)
    timeout_ms: int | None = None


class ProviderResponse(BaseModel):
    output: str
    model: str
    provider: str
    latency_ms: int | None = None
    usage: dict = Field(default_factory=dict)
    finish_reason: str | None = None
    metadata: dict = Field(default_factory=dict)


class ProviderError(BaseModel):
    error_type: str
    error_message: str
    provider: str
    model: str = "unknown"
    retryable: bool = False
    metadata: dict = Field(default_factory=dict)
