"""In-memory idempotency guard for single-process use.

V1.7 — MVP contract. Not distributed, not durable across restarts.
Provides scoped idempotency_key deduplication and sequence_index
validation for conversation message/run APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ── Context ────────────────────────────────────────────────────────


@dataclass
class IdempotencyContext:
    idempotency_key: str | None = None
    request_id: str | None = None
    sequence_index: int | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    conversation_id: str | None = None
    action: str = ""  # "create_message" | "create_conversation_run"


# ── Record ─────────────────────────────────────────────────────────


@dataclass
class IdempotencyRecord:
    scoped_key: str
    idempotency_key: str
    resource_id: str = ""
    resource_type: str | None = None
    request_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    conversation_id: str | None = None
    action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ── Decision ───────────────────────────────────────────────────────


class IdempotencyDecision(BaseModel):
    allowed: bool
    code: str
    reason: str = ""
    idempotency_key: str | None = None
    existing_resource_id: str | None = None
    existing_metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Guard ──────────────────────────────────────────────────────────


class IdempotencyGuard:
    """In-memory idempotency guard.

    Scoped key: tenant_id|user_id|conversation_id|action|idempotency_key
    Sequence scope: tenant_id|conversation_id

    Boundaries:
      - Single-process only
      - Not durable (lost on restart)
      - Not suitable for multi-instance deployment
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Clear all stored records and sequences (for test isolation)."""
        self._store: dict[str, IdempotencyRecord] = {}
        self._sequences: dict[str, int] = {}

    # ── Scoped key ─────────────────────────────────────────────

    @staticmethod
    def _build_scope_key(ctx: IdempotencyContext) -> str | None:
        if not ctx.idempotency_key:
            return None
        return "|".join([
            ctx.tenant_id or "",
            ctx.user_id or "",
            ctx.conversation_id or "",
            ctx.action or "",
            ctx.idempotency_key,
        ])

    @staticmethod
    def _seq_scope(ctx: IdempotencyContext) -> str:
        return f"{ctx.tenant_id or ''}|{ctx.conversation_id or ''}"

    # ── Check ──────────────────────────────────────────────────

    def check(self, ctx: IdempotencyContext) -> IdempotencyDecision:
        """Check if a request with this context can proceed."""

        # Legacy: no key, no sequence → skip
        if not ctx.idempotency_key and ctx.sequence_index is None:
            return IdempotencyDecision(
                allowed=True, code="LEGACY_SKIP",
                idempotency_key=None, request_id=ctx.request_id,
            )

        # Idempotency check
        if ctx.idempotency_key:
            scoped = self._build_scope_key(ctx)
            existing = self._store.get(scoped) if scoped else None
            if existing is not None:
                return IdempotencyDecision(
                    allowed=False,
                    code="DUPLICATE_IDEMPOTENCY_KEY",
                    reason=f"Duplicate idempotency_key '{ctx.idempotency_key}' "
                           f"for action '{ctx.action}'",
                    idempotency_key=ctx.idempotency_key,
                    existing_resource_id=existing.resource_id,
                    existing_metadata=existing.metadata,
                    request_id=ctx.request_id,
                )

        # Sequence check
        if ctx.sequence_index is not None:
            seq_key = self._seq_scope(ctx)
            current = self._sequences.get(seq_key, -1)
            if ctx.sequence_index <= current:
                return IdempotencyDecision(
                    allowed=False,
                    code="STALE_SEQUENCE",
                    reason=f"Stale sequence_index {ctx.sequence_index} "
                           f"(max known: {current})",
                    idempotency_key=ctx.idempotency_key,
                    request_id=ctx.request_id,
                )
            if ctx.sequence_index > current + 1:
                return IdempotencyDecision(
                    allowed=False,
                    code="SEQUENCE_GAP",
                    reason=f"Sequence gap: got {ctx.sequence_index}, "
                           f"expected ≤ {current + 1}",
                    idempotency_key=ctx.idempotency_key,
                    request_id=ctx.request_id,
                )

        return IdempotencyDecision(
            allowed=True, code="ALLOWED",
            idempotency_key=ctx.idempotency_key,
            request_id=ctx.request_id,
        )

    # ── Record ─────────────────────────────────────────────────

    def record(
        self,
        ctx: IdempotencyContext,
        resource_id: str,
        resource_type: str | None = None,
        extra_metadata: dict | None = None,
    ) -> None:
        """Record a successful idempotent operation."""
        if ctx.idempotency_key:
            scoped = self._build_scope_key(ctx)
            if scoped:
                meta = dict(extra_metadata or {})
                meta.setdefault("conversation_id", ctx.conversation_id)
                meta.setdefault("tenant_id", ctx.tenant_id)
                meta.setdefault("user_id", ctx.user_id)
                self._store[scoped] = IdempotencyRecord(
                    scoped_key=scoped,
                    idempotency_key=ctx.idempotency_key,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    request_id=ctx.request_id,
                    tenant_id=ctx.tenant_id,
                    user_id=ctx.user_id,
                    conversation_id=ctx.conversation_id,
                    action=ctx.action,
                    metadata=meta,
                )

        if ctx.sequence_index is not None:
            seq_key = self._seq_scope(ctx)
            current = self._sequences.get(seq_key, -1)
            if ctx.sequence_index > current:
                self._sequences[seq_key] = ctx.sequence_index

    # ── Lookup ─────────────────────────────────────────────────

    def get_existing(self, idempotency_key: str) -> IdempotencyRecord | None:
        """Return the record for a previously completed idempotency key.

        Note: this searches unscopped — primarily for testing.
        Use check() for production paths.
        """
        for rec in self._store.values():
            if rec.idempotency_key == idempotency_key:
                return rec
        return None


# Singleton for route-level use
idempotency_guard = IdempotencyGuard()
