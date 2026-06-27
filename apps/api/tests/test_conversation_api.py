"""Tests for V1.2 Conversation / Message API.

Uses TestClient against the running app with SQLite (test default).
All existing tests unchanged.
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _create_conv(user_id="user_abc", tenant_id="tenant_xyz"):
    return client.post("/api/conversations", json={
        "user_id": user_id,
        "tenant_id": tenant_id,
    }).json()


# ── Conversation CRUD ──────────────────────────────────────────────


def test_create_conversation() -> None:
    resp = client.post("/api/conversations", json={
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == "user_abc"
    assert data["tenant_id"] == "tenant_xyz"
    assert data["id"].startswith("conv_")
    assert "metadata" in data


def test_create_conversation_requires_user_id() -> None:
    resp = client.post("/api/conversations", json={"tenant_id": "t"})
    assert resp.status_code == 422


def test_create_conversation_requires_tenant_id() -> None:
    resp = client.post("/api/conversations", json={"user_id": "u"})
    assert resp.status_code == 422


def test_get_conversation() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == conv["id"]


def test_get_conversation_not_found() -> None:
    resp = client.get("/api/conversations/conv_nonexistent")
    assert resp.status_code == 404


def test_list_conversations_by_user() -> None:
    _create_conv(user_id="user_list")
    resp = client.get("/api/conversations?user_id=user_list")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_conversations_by_tenant() -> None:
    _create_conv(tenant_id="tenant_list")
    resp = client.get("/api/conversations?tenant_id=tenant_list")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_two_conversations_different_ids() -> None:
    c1 = _create_conv()
    c2 = _create_conv()
    assert c1["id"] != c2["id"]


# ── Message CRUD ───────────────────────────────────────────────────


def _create_msg(conv_id, role="user", content="hello"):
    return client.post(f"/api/conversations/{conv_id}/messages", json={
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
        "role": role,
        "content": content,
    }).json()


def test_add_message_user_role() -> None:
    conv = _create_conv()
    msg = _create_msg(conv["id"], role="user", content="Hello")
    assert msg["role"] == "user"
    assert msg["content"] == "Hello"
    assert msg["conversation_id"] == conv["id"]
    assert msg["user_id"] == "user_abc"
    assert msg["tenant_id"] == "tenant_xyz"


def test_add_message_all_roles() -> None:
    conv = _create_conv()
    for role in ("user", "assistant", "system", "tool"):
        msg = _create_msg(conv["id"], role=role, content=f"test_{role}")
        assert msg["role"] == role


def test_add_message_invalid_role() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": "u", "tenant_id": "t",
        "role": "admin", "content": "x",
    })
    assert resp.status_code == 422


def test_message_metadata_round_trip() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": "u", "tenant_id": "t",
        "role": "user", "content": "with meta",
        "metadata": {"source": "test", "version": 1},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["metadata"]["source"] == "test"
    assert data["metadata"]["version"] == 1


def test_list_messages_stable_order() -> None:
    conv = _create_conv()
    ids = []
    for i in range(3):
        msg = _create_msg(conv["id"], role="user", content=f"msg_{i}")
        ids.append(msg["id"])

    resp = client.get(f"/api/conversations/{conv['id']}/messages")
    assert resp.status_code == 200
    returned = [m["id"] for m in resp.json()]
    assert returned == ids  # insertion order preserved


def test_list_messages_empty() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_message_to_nonexistent_conversation() -> None:
    resp = client.post("/api/conversations/conv_nonexist/messages", json={
        "user_id": "u", "tenant_id": "t", "role": "user", "content": "x",
    })
    assert resp.status_code == 404


# ── Conversation Run ───────────────────────────────────────────────


def test_conversation_run_creates_user_message() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
        "input": "hello",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["conversation_id"] == conv["id"]
    assert data["user_message_id"].startswith("msg_")
    assert data["run_id"].startswith("run_")


def test_conversation_run_metadata_binding() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
        "input": "binding test",
    })
    assert resp.status_code == 201
    data = resp.json()

    # Verify run metadata has user context
    run_resp = client.get(f"/api/runs/{data['run_id']}")
    assert run_resp.status_code == 200
    run = run_resp.json()
    meta = run.get("metadata", {})
    assert meta.get("user_id") == "user_abc"
    assert meta.get("tenant_id") == "tenant_xyz"
    assert meta.get("conversation_id") == conv["id"]
    assert meta.get("message_id") == data["user_message_id"]


def test_conversation_run_assistant_message_written() -> None:
    """When run completes with output, assistant message is written."""
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": "user_abc",
        "tenant_id": "tenant_xyz",
        "input": "hello",
    })
    assert resp.status_code == 201
    data = resp.json()
    # Run should complete with demo_agent
    assert data["run_status"] == "completed"
    assert data["assistant_message_id"] is not None

    # Verify assistant message exists with run output
    msgs = client.get(f"/api/conversations/{conv['id']}/messages").json()
    roles = [m["role"] for m in msgs]
    assert roles == ["user", "assistant"]
    assert msgs[1]["run_id"] == data["run_id"]
    assert msgs[1]["content"] != ""


def test_conversation_run_user_tenant_mismatch() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": "wrong_user",
        "tenant_id": "tenant_xyz",
        "input": "hello",
    })
    assert resp.status_code == 400


def test_conversation_run_nonexistent() -> None:
    resp = client.post("/api/conversations/conv_nonexist/runs", json={
        "user_id": "u", "tenant_id": "t", "input": "hello",
    })
    assert resp.status_code == 400


# ── Backward compatibility ─────────────────────────────────────────


def test_old_runs_endpoint_unchanged() -> None:
    """Old POST /api/runs without user context still works."""
    resp = client.post("/api/runs", json={"input": "old style"})
    assert resp.status_code == 201
    run = resp.json()
    assert run["status"] == "completed"
    # No user context in metadata
    meta = run.get("metadata", {})
    assert "user_id" not in meta
    assert "tenant_id" not in meta
