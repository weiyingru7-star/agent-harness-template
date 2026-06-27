# Concurrency / Idempotency Contract 并发与幂等契约

V1.7 增加 `idempotency_key` 和 `sequence_index` 幂等/并发控制。
使用 in-memory `IdempotencyGuard`，适用于单进程和测试场景。

## V1.7 范围

### 当前支持

- ✅ Scoped idempotency key（含 tenant / user / conversation / action）
- ✅ 重复 key 检测（返回已有 resource，不重复创建）
- ✅ Sequence index 校验（stale / gap 检测）
- ✅ Request ID 透传
- ✅ Tenant/conversation 作用域隔离
- ✅ Legacy 兼容（不传 key/seq 时跳过校验）
- ✅ In-memory guard（单进程 MVP）

### 当前不支持

- ❌ Redis / 分布式锁
- ❌ Worker / 异步队列
- ❌ 生产级 Exactly-once
- ❌ 工具调用幂等（预留 V1.8）
- ❌ Webhook 去重

## Core Design 核心设计

### Scoped Key 作用域键

Idempotency key 不能全局去重。V1.7 使用 scoped key：

```
scoped_key = tenant_id | user_id | conversation_id | action | idempotency_key
```

避免不同 tenant / conversation / action 使用相同 key 时冲突。

### Sequence Scope 序列作用域

```
sequence_scope = tenant_id | conversation_id
```

Sequence 按 tenant + conversation 独立追踪。

### IdempotencyDecision 决策

| Code | Allowed | 说明 |
|---|---|---|
| `LEGACY_SKIP` | true | 未传 key/seq，跳过校验 |
| `ALLOWED` | true | 可继续执行 |
| `DUPLICATE_IDEMPOTENCY_KEY` | false | 重复键，返回已有 resource |
| `STALE_SEQUENCE` | false | sequence ≤ 已有最大值 |
| `SEQUENCE_GAP` | false | sequence > 最大值+1 |

## Message API 幂等

```bash
# 第一次：创建 message
curl -X POST /api/conversations/{id}/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u1", "tenant_id": "t1",
    "role": "user", "content": "Hello",
    "idempotency_key": "msg_001"
  }'
# → 201, message created

# 第二次（相同 key）：返回已有 message
curl -X POST /api/conversations/{id}/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u1", "tenant_id": "t1",
    "role": "user", "content": "Hello",
    "idempotency_key": "msg_001"
  }'
# → 201 (with existing message data, no duplicate created)
```

## Conversation Run 幂等

```bash
# 第一次：创建 run
curl -X POST /api/conversations/{id}/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u1", "tenant_id": "t1",
    "input": "hello",
    "idempotency_key": "run_001"
  }'
# → 201, run created

# 第二次（相同 key）：返回已有 run response
curl -X POST /api/conversations/{id}/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u1", "tenant_id": "t1",
    "input": "hello",
    "idempotency_key": "run_001"
  }'
# → 201 (with existing run data, no second run created)
```

## Sequence Index 示例

```bash
# 按顺序发送消息
curl -X POST /api/conversations/{id}/messages \
  -d '{"role":"user","content":"First","sequence_index":0}'
# → 201

curl -X POST /api/conversations/{id}/messages \
  -d '{"role":"user","content":"Second","sequence_index":1}'
# → 201

# 重复旧 sequence → 409 STALE_SEQUENCE
curl -X POST /api/conversations/{id}/messages \
  -d '{"role":"user","content":"Duplicate","sequence_index":0}'
# → 409

# 跳过大 gap → 409 SEQUENCE_GAP
curl -X POST /api/conversations/{id}/messages \
  -d '{"role":"user","content":"Jump","sequence_index":99}'
# → 409
```

## Guard 边界

V1.7 `IdempotencyGuard` 是 **MVP 实现**：

- ✅ 单进程 in-memory 存储
- ✅ 测试和轻量开发使用
- ❌ 进程重启后丢失记录
- ❌ 多实例部署不可靠
- ❌ 不提供生产级 exactly-once

生产部署应替换为 DB / Redis 实现。

## 后续版本

| 版本 | 内容 |
|---|---|
| V1.8 | Async Job Queue / Worker Runtime |
