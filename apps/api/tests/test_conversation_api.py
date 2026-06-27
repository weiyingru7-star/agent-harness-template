"""Tests for V1.2 Conversation / Message API and V1.3 Tenant Isolation.

Uses TestClient against the running app (SQLite test default).
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

_TENANT = "tenant_xyz"
_USER = "user_abc"


def _create_conv(user_id=_USER, tenant_id=_TENANT):
    return client.post("/api/conversations", json={
        "user_id": user_id, "tenant_id": tenant_id,
    }).json()


# ── Conversation CRUD ──────────────────────────────────────────────


def test_create_conversation() -> None:
    resp = client.post("/api/conversations", json={
        "user_id": _USER, "tenant_id": _TENANT,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == _USER
    assert data["tenant_id"] == _TENANT
    assert data["id"].startswith("conv_")
    assert "metadata" in data


def test_create_conversation_requires_user_id() -> None:
    resp = client.post("/api/conversations", json={"tenant_id": "t"})
    assert resp.status_code == 422


def test_create_conversation_requires_tenant_id() -> None:
    resp = client.post("/api/conversations", json={"user_id": "u"})
    assert resp.status_code == 422


def test_get_conversation_own_tenant() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}?tenant_id={_TENANT}")
    assert resp.status_code == 200
    assert resp.json()["id"] == conv["id"]


def test_get_conversation_without_tenant_400() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}")
    assert resp.status_code == 400


def test_get_conversation_wrong_tenant_404() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}?tenant_id=wrong_tenant")
    assert resp.status_code == 404


def test_get_conversation_not_found() -> None:
    resp = client.get(f"/api/conversations/conv_nonexistent?tenant_id={_TENANT}")
    assert resp.status_code == 404


def test_list_conversations_tenant_only() -> None:
    _create_conv()
    resp = client.get(f"/api/conversations?tenant_id={_TENANT}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_conversations_user_and_tenant() -> None:
    _create_conv()
    resp = client.get(f"/api/conversations?tenant_id={_TENANT}&user_id={_USER}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_conversations_without_tenant_400() -> None:
    resp = client.get("/api/conversations")
    assert resp.status_code == 400


def test_two_conversations_different_ids() -> None:
    c1 = _create_conv()
    c2 = _create_conv()
    assert c1["id"] != c2["id"]


# ── Message CRUD ───────────────────────────────────────────────────


def _create_msg(conv_id, role="user", content="hello"):
    resp = client.post(f"/api/conversations/{conv_id}/messages", json={
        "user_id": _USER, "tenant_id": _TENANT,
        "role": role, "content": content,
    })
    assert resp.status_code == 201
    return resp.json()


def test_add_message_own_tenant() -> None:
    conv = _create_conv()
    msg = _create_msg(conv["id"], role="user", content="Hello")
    assert msg["role"] == "user"
    assert msg["content"] == "Hello"
    assert msg["conversation_id"] == conv["id"]
    assert msg["user_id"] == _USER
    assert msg["tenant_id"] == _TENANT


def test_add_message_wrong_tenant_404() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": _USER, "tenant_id": "wrong_tenant",
        "role": "user", "content": "x",
    })
    assert resp.status_code == 404


def test_add_message_wrong_user_404() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": "wrong_user", "tenant_id": _TENANT,
        "role": "user", "content": "x",
    })
    assert resp.status_code == 404


def test_add_message_all_roles() -> None:
    conv = _create_conv()
    for role in ("user", "assistant", "system", "tool"):
        msg = _create_msg(conv["id"], role=role, content=f"test_{role}")
        assert msg["role"] == role


def test_add_message_invalid_role() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": _USER, "tenant_id": _TENANT,
        "role": "admin", "content": "x",
    })
    assert resp.status_code == 422


def test_message_metadata_round_trip() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/messages", json={
        "user_id": _USER, "tenant_id": _TENANT,
        "role": "user", "content": "with meta",
        "metadata": {"source": "test", "version": 1},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["metadata"]["source"] == "test"
    assert data["metadata"]["version"] == 1


def test_list_messages_own_tenant() -> None:
    conv = _create_conv()
    ids = []
    for i in range(3):
        msg = _create_msg(conv["id"], role="user", content=f"msg_{i}")
        ids.append(msg["id"])

    resp = client.get(f"/api/conversations/{conv['id']}/messages?tenant_id={_TENANT}")
    assert resp.status_code == 200
    returned = [m["id"] for m in resp.json()]
    assert returned == ids  # insertion order preserved


def test_list_messages_without_tenant_400() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}/messages")
    assert resp.status_code == 400


def test_list_messages_wrong_tenant_404() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}/messages?tenant_id=wrong_tenant")
    assert resp.status_code == 404


def test_list_messages_empty() -> None:
    conv = _create_conv()
    resp = client.get(f"/api/conversations/{conv['id']}/messages?tenant_id={_TENANT}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_message_to_nonexistent_conversation() -> None:
    resp = client.post("/api/conversations/conv_nonexist/messages", json={
        "user_id": _USER, "tenant_id": _TENANT, "role": "user", "content": "x",
    })
    assert resp.status_code == 404


# ── Conversation Run ───────────────────────────────────────────────


def test_conversation_run_own_tenant() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": _USER, "tenant_id": _TENANT, "input": "hello",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["conversation_id"] == conv["id"]
    assert data["user_message_id"].startswith("msg_")
    assert data["run_id"].startswith("run_")


def test_conversation_run_metadata_binding() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": _USER, "tenant_id": _TENANT, "input": "binding test",
    })
    assert resp.status_code == 201
    data = resp.json()

    run_resp = client.get(f"/api/runs/{data['run_id']}")
    assert run_resp.status_code == 200
    run = run_resp.json()
    meta = run.get("metadata", {})
    assert meta.get("user_id") == _USER
    assert meta.get("tenant_id") == _TENANT
    assert meta.get("conversation_id") == conv["id"]
    assert meta.get("message_id") == data["user_message_id"]


def test_conversation_run_assistant_message_written() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": _USER, "tenant_id": _TENANT, "input": "hello",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["run_status"] == "completed"
    assert data["assistant_message_id"] is not None

    msgs = client.get(f"/api/conversations/{conv['id']}/messages?tenant_id={_TENANT}").json()
    roles = [m["role"] for m in msgs]
    assert roles == ["user", "assistant"]
    assert msgs[1]["run_id"] == data["run_id"]
    assert msgs[1]["content"] != ""


def test_conversation_run_wrong_tenant_404() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": _USER, "tenant_id": "wrong_tenant", "input": "hello",
    })
    assert resp.status_code == 404


def test_conversation_run_wrong_user_404() -> None:
    conv = _create_conv()
    resp = client.post(f"/api/conversations/{conv['id']}/runs", json={
        "user_id": "wrong_user", "tenant_id": _TENANT, "input": "hello",
    })
    assert resp.status_code == 404


def test_conversation_run_nonexistent_404() -> None:
    resp = client.post("/api/conversations/conv_nonexist/runs", json={
        "user_id": _USER, "tenant_id": _TENANT, "input": "hello",
    })
    assert resp.status_code == 404


# ── Backward compatibility ─────────────────────────────────────────


def test_old_runs_endpoint_unchanged() -> None:
    resp = client.post("/api/runs", json={"input": "old style"})
    assert resp.status_code == 201
    run = resp.json()
    assert run["status"] == "completed"
    meta = run.get("metadata", {})
    assert "user_id" not in meta
    assert "tenant_id" not in meta
