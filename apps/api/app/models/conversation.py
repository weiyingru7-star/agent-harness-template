from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    agent_template_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None


class Message(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    user_id: str
    role: str
    content: str = ""
    run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


# ── Request / Response models ──────────────────────────────────────


class CreateConversationRequest(BaseModel):
    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    agent_template_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    agent_template_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None


class CreateMessageRequest(BaseModel):
    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    role: Literal["user", "assistant", "system", "tool"]
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    idempotency_key: str | None = None
    sequence_index: int | None = Field(default=None, ge=0)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    user_id: str
    role: str
    content: str = ""
    run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    idempotency_key: str | None = None
    sequence_index: int | None = None
    created_at: datetime


class CreateConversationRunRequest(BaseModel):
    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    input: str = Field(min_length=1)
    module_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    idempotency_key: str | None = None


class ConversationRunResponse(BaseModel):
    conversation_id: str
    user_message_id: str
    assistant_message_id: str | None = None
    run_id: str
    run_status: str
    request_id: str | None = None
    idempotency_key: str | None = None
