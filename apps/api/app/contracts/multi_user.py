"""Multi-user / multi-conversation runtime contracts.

V1.1 — contracts only, no auth, no RBAC, no tenant enforcement.
All new fields are optional for backward compatibility.
Concurrency fields (request_id, idempotency_key) are reserved for V1.6.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── UserContext ─────────────────────────────────────────────────────


class UserContext(BaseModel):
    """Identity context for multi-user operations.

    Required fields ensure every run can be attributed to a user
    and tenant. Roles are reserved for future RBAC.
    """

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    roles: list[str] = Field(default_factory=list)


# ── Conversation ────────────────────────────────────────────────────


class Conversation(BaseModel):
    """A multi-message conversation session."""

    conversation_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    agent_template_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Message ─────────────────────────────────────────────────────────


class Message(BaseModel):
    """A single message within a conversation.

    Concurrency fields (request_id, idempotency_key, sequence_index)
    are reserved for V1.6 and not enforced in V1.1.
    """

    message_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    role: Literal["user", "assistant", "system", "tool"]
    content: str = ""
    request_id: str | None = None          # reserved for V1.6
    idempotency_key: str | None = None     # reserved for V1.6
    sequence_index: int | None = Field(default=None, ge=0)  # reserved for V1.6
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── RunBinding ──────────────────────────────────────────────────────


class RunBinding(BaseModel):
    """Maps a run to user + conversation context."""

    run_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    conversation_id: str | None = None
    message_id: str | None = None
