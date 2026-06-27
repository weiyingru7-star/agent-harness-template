# Async Job Queue / Worker Runtime 异步任务队列与 Worker 运行时

V1.8 增加 DB 后台异步任务队列和 Worker Runtime MVP。

## Job 生命周期

```
         ┌──────────────────────────────────────┐
         │                                      │
         ▼                                      │
  queued ──→ running ──→ succeeded              │
              │                                  │
              ├──→ failed (retry exhausted)      │
              │                                  │
              └──→ queued (retry, attempts<max)──┘
  queued ──→ canceled (only queued)
```

**不允许的转换**：
- `running → canceled` — 返回 409 Conflict
- `succeeded/failed/canceled` → 任何状态 — terminal，不可变

## V1.8 范围

### 当前支持

- ✅ Job model（job_type / status / payload / result / error / attempts / max_attempts）
- ✅ 4 种 job status（queued / running / succeeded / failed / canceled）
- ✅ DB 持久化（SQLAlchemy + Base.metadata.create_all，无 migration）
- ✅ 幂等入队（scoped key：tenant_id + user_id + job_type + idempotency_key）
- ✅ 已有 job（任何状态）重复 key 返回已有 job，不创建 second
- ✅ WorkerRuntime.claim_next + handler dispatch
- ✅ Retry / max_attempts
- ✅ Cancel（仅 queued 状态）
- ✅ Tenant 过滤列表
- ✅ Template-safe handler: echo
- ✅ API: create / list / get / cancel
- ✅ CLI: `scripts/run_worker_once.py`

### 当前不支持

- ❌ Redis / 分布式队列
- ❌ 常驻 Worker Daemon
- ❌ 生产级 Exactly-once
- ❌ Scheduler / Cron
- ❌ 真实业务 handler
- ❌ Auth / RBAC
- ❌ Run-once API

## API Endpoints

### POST /api/jobs — 创建 job

```bash
curl -X POST http://localhost:8005/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "job_type": "echo",
    "payload": {"message": "hello"},
    "tenant_id": "t1",
    "user_id": "u1",
    "idempotency_key": "unique_key",
    "max_attempts": 1
  }'
```

### GET /api/jobs — 列表

```bash
curl "http://localhost:8005/api/jobs?tenant_id=t1"
```

### GET /api/jobs/{id} — 详情

```bash
curl "http://localhost:8005/api/jobs/job_xxx"
```

### POST /api/jobs/{id}/cancel — 取消

```bash
curl -X POST "http://localhost:8005/api/jobs/job_xxx/cancel"
```

仅 `queued` 状态的 job 可取消。`running` 返回 409。

## Idempotent Enqueue

Scoped key: `tenant_id | user_id | job_type | idempotency_key`

已有 job（任何状态）重复 key → 返回已有 job，不创建 second。

## Retry / max_attempts

| 场景 | 行为 |
|---|---|
| attempts < max_attempts | 失败后重新 queued |
| attempts >= max_attempts | 状态变为 failed（terminal） |
| max_attempts=1 (default) | 一次失败即 terminal |

## CLI Worker

```bash
python3 scripts/run_worker_once.py
```

Claim 一个 queued job 并执行。不是常驻 daemon。输出：`succeeded` / `failed: ...` / `idle`。

## Worker Handler 注册

```python
from app.services.worker_runtime import register_handler

def my_handler(payload):
    # process job
    return {"result": "ok"}

register_handler("my_job_type", my_handler)
```

内置 handler：`echo` — 直接返回 payload。

## 后续版本

| 版本 | 内容 |
|---|---|
| V2.0 | Document Versioning / Knowledge Base Update |
