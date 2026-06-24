# Agent Harness Template 通用 Agent 模板

这是一个**业务无关的通用 Agent Harness 模板**，用于未来快速构建可复用的 AI Agent 应用。

## Stage 1 Scope Stage 1 范围

当前 Stage 1 只包含：

- Next.js 前端首页
- FastAPI 后端 `/health`
- PostgreSQL 和 Redis 的 Docker Compose 配置
- `.env.example`
- Makefile
- README
- `AGENTS.md`
- `CLAUDE.md`
- 后端基础健康检查测试

Stage 1 明确不包含 agent runtime、runs、steps、events、AI Runtime、RAG、file upload 或 business modules。

## Requirements 环境要求

- Python 3.11+
- Node.js 20+
- Docker
- Make

## Setup 安装

```bash
cp .env.example .env
make install
```

## Start Infrastructure 启动基础设施

```bash
make up
```

该命令会启动 PostgreSQL 和 Redis。

默认使用非标准本地端口，尽量避免和本机已有服务冲突：

- PostgreSQL：`localhost:15432`
- Redis：`localhost:16379`

## Start Backend 启动后端

```bash
make dev-api
```

后端健康检查：

```bash
curl http://localhost:8005/health
```

预期返回：

```json
{
  "status": "ok",
  "service": "agent-harness-api"
}
```

## Start Frontend 启动前端

```bash
make dev-web
```

打开：

```text
http://localhost:3005
```

## Test 测试

```bash
make test-api
```

## Stage 2 Run Flow

Stage 2 adds a minimal Agent Run path using `modules/demo_agent`.
The demo agent returns a mock response and does not call a real LLM.

Create a run:

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}'
```

Read a run:

```bash
curl http://localhost:8005/api/runs/<run_id>
```

Read run events:

```bash
curl http://localhost:8005/api/runs/<run_id>/events
```

## Stop Infrastructure 停止基础设施

```bash
make down
```
