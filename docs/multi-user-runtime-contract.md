# Multi-User Runtime Contract 多用户运行时合同

V1.1 定义 UserContext / Conversation / Message / RunBinding 数据合同，
为 Agent Harness Template 增加多用户、多会话、多租户的上下文边界。
**V1.1 只做 contract，不做 auth，不做 RBAC，不做 enforcement。**

## Motivation 动机

当前 harness 已支持 run / trace / timeline / checkpoint / tool / rag / provider /
policy / scaffold，但缺少多用户 / 多会话边界。当项目被用于多人场景时：

- 用户 A 和用户 B 的 run 混在一起，无法区分归属
- Run / trace / checkpoint 缺少 user_id / tenant_id 标签
- 后续 RAG / tool 没有 tenant_id 约束
- 工具调用无法判断当前资源是否属于当前用户

V1.1 不做真实隔离，但为每个 run 提供明确的归属字段，为后续租户隔离打基础。

## Contracts 合同

### UserContext

```python
class UserContext(BaseModel):
    user_id: str               # 必填，非空
    tenant_id: str             # 必填，非空
    roles: list[str] = []      # 可选，预留 RBAC
```

### Conversation

```python
class Conversation(BaseModel):
    conversation_id: str       # 必填，非空
    tenant_id: str             # 必填，非空
    user_id: str               # 必填，非空
    agent_template_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    metadata: dict = {}
```

### Message

```python
class Message(BaseModel):
    message_id: str            # 必填，非空
    conversation_id: str       # 必填，非空
    tenant_id: str             # 必填，非空
    user_id: str               # 必填，非空
    role: Literal["user", "assistant", "system", "tool"]
    content: str = ""
    # 并发预留字段（V1.1 不 enforcement）
    request_id: str | None = None         # V1.6
    idempotency_key: str | None = None    # V1.6
    sequence_index: int | None = None     # V1.6
    created_at: datetime
    metadata: dict = {}
```

### RunBinding

```python
class RunBinding(BaseModel):
    run_id: str                # 必填，非空
    tenant_id: str             # 必填，非空
    user_id: str               # 必填，非空
    conversation_id: str | None = None
    message_id: str | None = None
```

## Run API 集成

CreateRunRequest 新增可选字段：

```python
class CreateRunRequest(BaseModel):
    input: str
    module_id: str | None = None
    user_id: str | None = None          # NEW — V1.1
    tenant_id: str | None = None        # NEW — V1.1
    conversation_id: str | None = None  # NEW — V1.1
    message_id: str | None = None       # NEW — V1.1
```

使用方式：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "hello",
    "user_id": "user_abc",
    "tenant_id": "tenant_xyz",
    "conversation_id": "conv_001",
    "message_id": "msg_001"
  }'
```

Run 响应不变（无顶层 user_id/tenant_id）。这些字段存储在 `run.metadata` 中：

```json
{
  "id": "run_xxx",
  "metadata": {
    "module_id": "demo_agent",
    "user_id": "user_abc",
    "tenant_id": "tenant_xyz",
    "conversation_id": "conv_001",
    "message_id": "msg_001"
  }
}
```

## V1.1 范围

### 当前支持

- ✅ UserContext contract（user_id / tenant_id / roles）
- ✅ Conversation contract（conversation_id / tenant_id / user_id / agent_template_id）
- ✅ Message contract（四角色：user / assistant / system / tool）
- ✅ RunBinding contract（run_id ↔ user + conversation）
- ✅ CreateRunRequest 可选传递 user context
- ✅ Run metadata 可保存 user / conversation binding
- ✅ 20 条 contract + API 兼容测试
- ✅ 所有 487 已有测试不变

### 当前不支持

- ❌ 认证（Auth / OAuth / JWT）
- ❌ 角色权限控制（RBAC）
- ❌ 租户隔离（Tenant enforcement）
- ❌ RAG tenant filter
- ❌ Tool permission guard
- ❌ Idempotency enforcement
- ❌ 并发锁 / 限流 / 队列
- ❌ 异步 Worker
- ❌ 真实业务 Agent

### 并发预留字段说明

Message contract 中包含 `request_id`、`idempotency_key`、`sequence_index` 字段。
这些字段预留用于 V1.6 Concurrency / Idempotency Contract。V1.1 不实现：

- 幂等去重
- 请求去重
- 消息顺序保证
- 并发锁
- 限流

## Future Versions 后续版本

| 版本 | 内容 |
|---|---|
| V1.1 | Multi-user runtime contracts（当前） |
| V1.2 | Message / Conversation API |
| V1.3 | Tenant Isolation |
| V1.4 | RAG Tenant Filter |
| V1.5 | Tool Permission / Ownership Guard |
| V1.6 | Concurrency / Idempotency Contract |
