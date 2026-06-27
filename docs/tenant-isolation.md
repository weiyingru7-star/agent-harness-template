# Tenant Isolation 租户隔离

V1.3 为 Conversation / Message API 增加了 tenant-level isolation。

## V1.3 范围

### 当前支持

- ✅ tenant_id required for all conversation/message operations
- ✅ missing tenant_id → 400 Bad Request
- ✅ tenant mismatch → 404 Not Found
- ✅ user_id consistency check for message/run operations
- ✅ list conversations scoped by tenant_id (optional user_id)
- ✅ run.metadata 继续携带 tenant_id / user_id / conversation_id / message_id
- ✅ 旧 `/api/runs` 完全不变

### 当前不支持（同 V1.1–V1.2）

- ❌ Auth / OAuth / JWT
- ❌ 角色权限控制（RBAC）
- ❌ RAG tenant filter（V1.4）
- ❌ Tool permission guard（V1.5）
- ❌ 高并发锁 / 限流 / 幂等 enforcement
- ❌ 完整 SaaS 权限模型

## Tenant 规则

| 操作 | tenant_id 来源 | missing→ | mismatch→ |
|---|---|---|---|
| `GET /api/conversations` | query `?tenant_id=` | 400 | 400（无法 query） |
| `GET /api/conversations/{id}` | query `?tenant_id=` | 400 | 404 |
| `POST /api/conversations/{id}/messages` | body `tenant_id` | Pydantic 校验 | 404 |
| `GET /api/conversations/{id}/messages` | query `?tenant_id=` | 400 | 404 |
| `POST /api/conversations/{id}/runs` | body `tenant_id` | Pydantic 校验 | 404 |

**user_id 一致性**：

- `POST /api/conversations/{id}/messages` 要求 `request.user_id == conversation.user_id`
- `POST /api/conversations/{id}/runs` 要求 `request.user_id == conversation.user_id`
- V1.3 不支持 shared conversation

**404 vs 400**：

- `tenant_id` **缺失** → 400。这是请求参数错误，客户端应该修复。
- `tenant_id` **不匹配** → 404。避免泄露资源是否存在。

## API 使用示例

```bash
# 查询 conversations（必须指定 tenant）
curl "http://localhost:8005/api/conversations?tenant_id=tenant_xyz"

# 查询 conversation（必须指定 tenant）
curl "http://localhost:8005/api/conversations/conv_xxx?tenant_id=tenant_xyz"

# 查询 messages（必须指定 tenant）
curl "http://localhost:8005/api/conversations/conv_xxx/messages?tenant_id=tenant_xyz"

# 创建 message（body tenant_id 必须匹配 conversation）
curl -X POST "http://localhost:8005/api/conversations/conv_xxx/messages" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user_abc",
    "tenant_id": "tenant_xyz",
    "role": "user",
    "content": "hello"
  }'

# 创建 conversation run（body tenant_id 必须匹配 conversation）
curl -X POST "http://localhost:8005/api/conversations/conv_xxx/runs" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "user_abc",
    "tenant_id": "tenant_xyz",
    "input": "hello"
  }'
```

## 关于 auth

V1.3 不做 auth。tenant_id 由客户端传入，生产环境中应通过 auth layer
（JWT、OAuth 等）注入，但不在 V1.3 实现范围内。

## 后续版本

| 版本 | 内容 |
|---|---|
| V1.3 | Tenant Isolation（当前） |
| V1.4 | RAG Tenant Filter |
| V1.5 | Tool Permission / Ownership Guard |
| V1.6 | Concurrency / Idempotency Contract |
