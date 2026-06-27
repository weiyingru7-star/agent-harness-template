# Conversation / Message API 会话与消息 API

V1.2 在 V1.1 多用户合同基础上，实现了 Conversation / Message / Conversation Run API。
让 harness 支持基础多轮会话能力。

## V1.2 范围

### 当前支持

- ✅ Conversation CRUD（POST/GET/list）
- ✅ Message CRUD（POST/list，4 种角色）
- ✅ Conversation-triggered Run（user message → run → assistant message）
- ✅ user_id / tenant_id / conversation_id / message_id 归属链路
- ✅ 新表自动创建（`Base.metadata.create_all`，无迁移）
- ✅ 旧 `/api/runs` 完全不变
- ✅ 21 条新测试

### 当前不支持（同 V1.1）

- ❌ 认证（Auth / OAuth / JWT）
- ❌ 角色权限控制（RBAC）
- ❌ 完整租户隔离（Tenant enforcement）
- ❌ RAG tenant filter
- ❌ Tool permission guard / ownership
- ❌ 高并发锁 / 限流 / 幂等 enforcement
- ❌ 异步 Worker / 队列
- ❌ 真实业务 Agent

## API 参考

### Create Conversation

```http
POST /api/conversations
Content-Type: application/json

{
  "user_id": "user_abc",
  "tenant_id": "tenant_xyz",
  "agent_template_id": null
}
```

Response `201`:
```json
{
  "id": "conv_xxx",
  "user_id": "user_abc",
  "tenant_id": "tenant_xyz",
  "agent_template_id": null,
  "metadata": {},
  "created_at": "...",
  "updated_at": null
}
```

### List Conversations

```http
GET /api/conversations?user_id=user_abc
GET /api/conversations?tenant_id=tenant_xyz
```

### Get Conversation

```http
GET /api/conversations/{conversation_id}
```

### Add Message

```http
POST /api/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "user_id": "user_abc",
  "tenant_id": "tenant_xyz",
  "role": "user",
  "content": "Hello",
  "metadata": {}
}
```

Roles: `user`, `assistant`, `system`, `tool`

### List Messages

```http
GET /api/conversations/{conversation_id}/messages
```

Messages are returned in insertion order (stable sort by `created_at`, `id`).

### Create Conversation Run

```http
POST /api/conversations/{conversation_id}/runs
Content-Type: application/json

{
  "user_id": "user_abc",
  "tenant_id": "tenant_xyz",
  "input": "what is agent harness"
}
```

Response includes:
- `user_message_id` — the user input message
- `assistant_message_id` — only present when run completes with output
- `run_id` — the created run
- `run_status` — final run status

## Conversation Run 流程

```
POST /api/conversations/{id}/runs
  │
  ├── 1. Validate conversation exists + user_id/tenant_id match
  ├── 2. Create Message(role="user", content=input)
  ├── 3. Create run_store.create_run(...)
  │      └── run.metadata = {user_id, tenant_id, conversation_id, message_id}
  └── 4. If run.status == "completed" and run.output exists:
         └── Create Message(role="assistant", content=run.output, run_id=run.id)
```

**Assistant message 写回策略**:
- 只在 run completed 且有 output 时写入 assistant message
- 如果 run failed / no output，不写 assistant message
- 不改变旧 `/api/runs` 行为
- 不改变 run lifecycle

## 用户身份 Consistency Check

`POST /api/conversations/{id}/runs` 中如果 `request.user_id` / `tenant_id`
与 conversation 记录不一致，请求会被拒绝（HTTP 400）。

**这不是完整 Tenant Enforcement**。V1.3 才做 Tenant Isolation。
V1.2 的 check 只是防止最基本的跨用户误用。

## DB

新表（自动创建，无迁移）：

```sql
conversations -- id, user_id, tenant_id, agent_template_id, metadata, created_at, updated_at
messages      -- id, conversation_id(FK), tenant_id, user_id, role, content, run_id, metadata, created_at
```

## 后续版本

| 版本 | 内容 |
|---|---|
| V1.2 | Message / Conversation API（当前） |
| V1.3 | Tenant Isolation |
| V1.4 | RAG Tenant Filter |
| V1.5 | Tool Permission / Ownership Guard |
| V1.6 | Concurrency / Idempotency Contract |
