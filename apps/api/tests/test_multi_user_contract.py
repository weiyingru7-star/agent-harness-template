"""Tests for V1.1 multi-user runtime contracts.

Run API tests use TestClient — user context fields are optional,
so all existing test behaviour is preserved.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.contracts.multi_user import (
    Conversation,
    Message,
    RunBinding,
    UserContext,
)
from app.main import app


client = TestClient(app)


# ── UserContext ─────────────────────────────────────────────────────


def test_user_context_valid() -> None:
    ctx = UserContext(user_id="user_abc", tenant_id="tenant_xyz")
    assert ctx.user_id == "user_abc"
    assert ctx.tenant_id == "tenant_xyz"
    assert ctx.roles == []


def test_user_context_empty_user_id_rejected() -> None:
    with pytest.raises(ValidationError):
        UserContext(user_id="", tenant_id="tenant_xyz")


def test_user_context_empty_tenant_id_rejected() -> None:
    with pytest.raises(ValidationError):
        UserContext(user_id="user_abc", tenant_id="")


def test_user_context_roles_defaults_empty() -> None:
    ctx = UserContext(user_id="u1", tenant_id="t1")
    assert ctx.roles == []


# ── Conversation ────────────────────────────────────────────────────


def test_conversation_valid() -> None:
    conv = Conversation(
        conversation_id="conv_001",
        tenant_id="tenant_xyz",
        user_id="user_abc",
    )
    assert conv.conversation_id == "conv_001"
    assert conv.tenant_id == "tenant_xyz"
    assert conv.user_id == "user_abc"


def test_conversation_empty_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Conversation(conversation_id="", tenant_id="t1", user_id="u1")
    with pytest.raises(ValidationError):
        Conversation(conversation_id="c1", tenant_id="", user_id="u1")
    with pytest.raises(ValidationError):
        Conversation(conversation_id="c1", tenant_id="t1", user_id="")


def test_conversation_agent_template_id_optional() -> None:
    conv = Conversation(conversation_id="c1", tenant_id="t1", user_id="u1")
    assert conv.agent_template_id is None

    conv2 = Conversation(
        conversation_id="c2", tenant_id="t1", user_id="u1",
        agent_template_id="generic_agent",
    )
    assert conv2.agent_template_id == "generic_agent"


# ── Message ─────────────────────────────────────────────────────────


def test_message_all_roles_accepted() -> None:
    for role in ("user", "assistant", "system", "tool"):
        msg = Message(
            message_id="m1", conversation_id="c1",
            tenant_id="t1", user_id="u1", role=role,
        )
        assert msg.role == role


def test_message_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(
            message_id="m1", conversation_id="c1",
            tenant_id="t1", user_id="u1", role="admin",
        )


def test_message_empty_content_allowed() -> None:
    msg = Message(
        message_id="m1", conversation_id="c1",
        tenant_id="t1", user_id="u1", role="user",
        content="",
    )
    assert msg.content == ""


def test_message_concurrency_fields_reserved() -> None:
    msg = Message(
        message_id="m1", conversation_id="c1",
        tenant_id="t1", user_id="u1", role="user",
        request_id="req_001",
        idempotency_key="idem_001",
        sequence_index=3,
    )
    assert msg.request_id == "req_001"
    assert msg.idempotency_key == "idem_001"
    assert msg.sequence_index == 3


def test_message_negative_sequence_index_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(
            message_id="m1", conversation_id="c1",
            tenant_id="t1", user_id="u1", role="user",
            sequence_index=-1,
        )


# ── RunBinding ──────────────────────────────────────────────────────


def test_run_binding_valid() -> None:
    rb = RunBinding(run_id="run_001", tenant_id="t1", user_id="u1")
    assert rb.run_id == "run_001"
    assert rb.tenant_id == "t1"
    assert rb.user_id == "u1"


def test_run_binding_optional_fields_none() -> None:
    rb = RunBinding(run_id="run_001", tenant_id="t1", user_id="u1")
    assert rb.conversation_id is None
    assert rb.message_id is None


def test_run_binding_with_conversation() -> None:
    rb = RunBinding(
        run_id="run_001", tenant_id="t1", user_id="u1",
        conversation_id="conv_001", message_id="msg_001",
    )
    assert rb.conversation_id == "conv_001"
    assert rb.message_id == "msg_001"


# ── Run API backward compatibility ─────────────────────────────────


def test_create_run_without_user_context() -> None:
    """Old request format (no user fields) still works."""
    response = client.post("/api/runs", json={"input": "hello"})
    assert response.status_code == 201
    run = response.json()
    assert run["status"] in ("completed", "running", "failed")


def test_create_run_with_user_context() -> None:
    """Run created with user context stores fields in metadata."""
    response = client.post("/api/runs", json={
        "input": "hello",
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
        "conversation_id": "conv_001",
        "message_id": "msg_001",
    })
    assert response.status_code == 201
    run = response.json()
    meta = run.get("metadata", {})
    assert meta.get("user_id") == "user_abc"
    assert meta.get("tenant_id") == "tenant_xyz"
    assert meta.get("conversation_id") == "conv_001"
    assert meta.get("message_id") == "msg_001"


def test_run_response_no_new_top_level_fields() -> None:
    """The Run API response does not add user_id/tenant_id at top level."""
    response = client.post("/api/runs", json={
        "input": "hello",
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
    })
    assert response.status_code == 201
    run = response.json()
    # user_id and tenant_id should NOT be top-level fields
    assert "user_id" not in run
    assert "tenant_id" not in run
    # They should only be in metadata
    assert run.get("metadata", {}).get("user_id") == "user_abc"


def test_two_conversations_different_ids() -> None:
    """Two Conversation instances have different IDs."""
    c1 = Conversation(conversation_id="conv_a", tenant_id="t1", user_id="u1")
    c2 = Conversation(conversation_id="conv_b", tenant_id="t1", user_id="u1")
    assert c1.conversation_id != c2.conversation_id


def test_contract_importable() -> None:
    from app.contracts import UserContext as UC, Conversation as C, Message as M, RunBinding as RB
    assert UC is UserContext
    assert C is Conversation
    assert M is Message
    assert RB is RunBinding
