"""Tests for V1.7 IdempotencyGuard — unit tests.

Each test creates a fresh guard instance for isolation.
"""

import pytest

from app.services.idempotency_guard import (
    IdempotencyContext,
    IdempotencyGuard,
)


def _ctx(**kwargs):
    """Helper to create IdempotencyContext with defaults."""
    defaults = {
        "idempotency_key": None,
        "request_id": None,
        "sequence_index": None,
        "tenant_id": "t1",
        "user_id": "u1",
        "conversation_id": "conv_001",
        "action": "create_message",
    }
    defaults.update(kwargs)
    return IdempotencyContext(**defaults)


@pytest.fixture
def guard() -> IdempotencyGuard:
    return IdempotencyGuard()


# ── Legacy skip ────────────────────────────────────────────────────


def test_legacy_skip(guard: IdempotencyGuard) -> None:
    """No key and no sequence → LEGACY_SKIP."""
    ctx = _ctx(idempotency_key=None, sequence_index=None)
    decision = guard.check(ctx)
    assert decision.allowed
    assert decision.code == "LEGACY_SKIP"


# ── Fresh key allowed ──────────────────────────────────────────────


def test_fresh_key_allowed(guard: IdempotencyGuard) -> None:
    """New idempotency_key → ALLOWED."""
    ctx = _ctx(idempotency_key="key_001")
    decision = guard.check(ctx)
    assert decision.allowed
    assert decision.code == "ALLOWED"


# ── Duplicate key ──────────────────────────────────────────────────


def test_duplicate_key_detected(guard: IdempotencyGuard) -> None:
    """Same scoped key twice → DUPLICATE_IDEMPOTENCY_KEY."""
    ctx = _ctx(idempotency_key="dup_key")
    guard.record(ctx, resource_id="msg_001")
    decision = guard.check(ctx)
    assert not decision.allowed
    assert decision.code == "DUPLICATE_IDEMPOTENCY_KEY"
    assert decision.existing_resource_id == "msg_001"


def test_duplicate_returns_existing_metadata(guard: IdempotencyGuard) -> None:
    """Duplicate includes existing_metadata with stored values."""
    ctx = _ctx(idempotency_key="meta_key", action="create_conversation_run")
    guard.record(ctx, resource_id="run_001", resource_type="conversation_run",
                 extra_metadata={"run_id": "run_001", "run_status": "completed"})
    decision = guard.check(ctx)
    assert not decision.allowed
    assert decision.existing_metadata.get("run_id") == "run_001"
    assert decision.existing_metadata.get("run_status") == "completed"


# ── Cross-scope isolation ──────────────────────────────────────────


def test_same_key_different_tenant_no_conflict(guard: IdempotencyGuard) -> None:
    """Same idempotency_key in different tenant → no conflict."""
    ctx_a = _ctx(tenant_id="t_a", idempotency_key="shared_key")
    ctx_b = _ctx(tenant_id="t_b", idempotency_key="shared_key")
    guard.record(ctx_a, resource_id="msg_a")
    decision = guard.check(ctx_b)
    assert decision.allowed
    assert decision.code == "ALLOWED"


def test_same_key_different_conversation_no_conflict(guard: IdempotencyGuard) -> None:
    """Same idempotency_key in different conversation → no conflict."""
    ctx_a = _ctx(conversation_id="conv_a", idempotency_key="key_x")
    ctx_b = _ctx(conversation_id="conv_b", idempotency_key="key_x")
    guard.record(ctx_a, resource_id="msg_a")
    decision = guard.check(ctx_b)
    assert decision.allowed


def test_same_key_different_action_no_conflict(guard: IdempotencyGuard) -> None:
    """Same idempotency_key for different action → no conflict."""
    ctx_msg = _ctx(idempotency_key="key_y", action="create_message")
    ctx_run = _ctx(idempotency_key="key_y", action="create_conversation_run")
    guard.record(ctx_msg, resource_id="msg_001")
    decision = guard.check(ctx_run)
    assert decision.allowed


# ── Sequence ───────────────────────────────────────────────────────


def test_sequence_increasing_allowed(guard: IdempotencyGuard) -> None:
    """seq_index 0 then 1 → both ALLOWED."""
    ctx0 = _ctx(sequence_index=0)
    ctx1 = _ctx(sequence_index=1)
    assert guard.check(ctx0).allowed
    guard.record(ctx0, resource_id="msg_0")
    assert guard.check(ctx1).allowed
    guard.record(ctx1, resource_id="msg_1")


def test_stale_sequence_denied(guard: IdempotencyGuard) -> None:
    """seq_index ≤ max → STALE_SEQUENCE."""
    ctx1 = _ctx(sequence_index=1)
    guard.record(ctx1, resource_id="msg_1")
    ctx0 = _ctx(sequence_index=0)
    decision = guard.check(ctx0)
    assert not decision.allowed
    assert decision.code == "STALE_SEQUENCE"


def test_sequence_gap_denied(guard: IdempotencyGuard) -> None:
    """seq_index > max+1 → SEQUENCE_GAP."""
    ctx0 = _ctx(sequence_index=0)
    guard.record(ctx0, resource_id="msg_0")
    ctx5 = _ctx(sequence_index=5)
    decision = guard.check(ctx5)
    assert not decision.allowed
    assert decision.code == "SEQUENCE_GAP"


def test_sequence_scoped_by_tenant(guard: IdempotencyGuard) -> None:
    """Same sequence in different tenants → independent tracking."""
    ctx_t1 = _ctx(tenant_id="t1", sequence_index=0)
    ctx_t2 = _ctx(tenant_id="t2", sequence_index=0)
    guard.record(ctx_t1, resource_id="msg_t1")
    decision = guard.check(ctx_t2)
    assert decision.allowed  # t2's seq=0 is fresh in its own scope


# ── Record + verify ────────────────────────────────────────────────


def test_record_then_duplicate(guard: IdempotencyGuard) -> None:
    """After record, check returns duplicate."""
    ctx = _ctx(idempotency_key="record_test")
    guard.record(ctx, resource_id="msg_r")
    decision = guard.check(ctx)
    assert not decision.allowed
    assert decision.code == "DUPLICATE_IDEMPOTENCY_KEY"


def test_request_id_passthrough(guard: IdempotencyGuard) -> None:
    """request_id flows through check and record."""
    ctx = _ctx(idempotency_key="rid_test", request_id="req_001")
    decision = guard.check(ctx)
    assert decision.request_id == "req_001"


# ── Guard reset ────────────────────────────────────────────────────


def test_reset_clears_store(guard: IdempotencyGuard) -> None:
    """reset() clears all stored records."""
    ctx = _ctx(idempotency_key="reset_me")
    guard.record(ctx, resource_id="msg_001")
    guard.reset()
    decision = guard.check(ctx)
    assert decision.allowed
