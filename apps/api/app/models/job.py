from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(BaseModel):
    id: str
    job_type: str
    status: str = "queued"
    tenant_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    idempotency_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    attempts: int = 0
    max_attempts: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CreateJobRequest(BaseModel):
    job_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    idempotency_key: str | None = None
    max_attempts: int = Field(default=1, ge=1, le=5)
