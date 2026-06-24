# Agent Harness Template 通用 Agent 模板

这是一个**业务无关的通用 Agent Harness 模板**，用于未来快速构建可复用的 AI Agent 应用。

## V0.1.0 Current Capabilities 当前能力

V0.1.0 已完成通用 Agent 底座的最小可运行闭环：

- Next.js 前端和 FastAPI 后端。
- PostgreSQL 和 Redis 本地基础设施。
- Agent Run 主链路：Run、Step、Event。
- Mock AI Runtime 和 registry。
- `.txt` / `.md` 文件上传。
- File 与 Artifact 最小模型。
- demo agent 最小状态机。
- 基于已上传文本文件的简单知识检索和 citation。
- module scaffold 脚手架。
- V0 总体验收和新模块创建文档。

## V0.1.1 Blueprint Alignment 蓝图对齐

V0.1.1 只补齐通用底座目录结构和文档，不改变现有 API 行为，不移动可运行代码，不实现复杂新功能。

新增蓝图目录包括：

- `core/config/`
- `core/db/`
- `core/cache/`
- `core/security/`
- `core/observability/`
- `core/utils/`
- `ai_runtime/`
- `harness/runtime/`
- `harness/workflow/`
- `harness/memory/`
- `harness/files/`
- `harness/multimodal/`
- `harness/policies/`
- `harness/events/`
- `schemas/`
- `evals/`
- `infra/`

这些目录当前主要包含 README，用于说明未来边界。它们不代表已经实现真实外部模型、embedding、向量数据库、多模态、人审、权限系统或 Eval Runner。

## V0.1.3 Schema Contracts 核心契约

V0.1.3 为核心对象补齐最小 JSON Schema 草案，方便后续模块、工具、技能、workflow 和 eval 按统一规范开发。

Schema 位于：

```text
schemas/
```

这些 schema 只作为通用契约草案，不改变现有 API 行为，不引入运行时强制校验，也不代表新增功能。

Schema 说明：

- [Schema Contracts 核心契约](docs/schema-contracts.md)

更多说明：

- [Architecture 架构说明](docs/architecture.md)
- [Agent Runtime](docs/agent-runtime.md)
- [AI Runtime](docs/ai-runtime.md)
- [Module Development](docs/module-development.md)
- [Workflow Execution](docs/workflow-execution.md)
- [Human Review](docs/human-review.md)
- [Observability](docs/observability.md)
- [Evals](docs/evals.md)
- [V0 总体验收](docs/v0-acceptance.md)
- [创建新 Agent](docs/how-to-create-new-agent.md)

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

## V0 Quick Start V0 快速开始

启动基础设施：

```bash
make up
```

启动后端：

```bash
make dev-api
```

后端地址：

```text
http://localhost:8005
```

启动前端：

```bash
make dev-web
```

前端地址：

```text
http://localhost:3005
```

创建 Run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID
curl http://localhost:8005/api/runs/$RUN_ID/events
```

上传文件并查看 File：

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/files/$FILE_ID
```

RAG ingest / retrieve：

```bash
curl -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}"

curl -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"Agent Harness","limit":3}'
```

scaffold 新模块：

```bash
python3 cli/scaffold_module.py sample_agent
```

更多文档：

- [V0 总体验收](docs/v0-acceptance.md)
- [创建新 Agent](docs/how-to-create-new-agent.md)

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
The demo agent returns a mock response and does not call a real external model.

Create a run:

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

Read a run:

```bash
curl http://localhost:8005/api/runs/$RUN_ID
```

Read run events:

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

## Stage 3 AI Runtime And Registries

Stage 3 adds a minimal AI runtime and static local registries.
The default LLM provider is `mock`. The OpenAI-compatible provider is present as
a basic adapter, but the run flow does not depend on a real API.

List local registries:

```bash
curl http://localhost:8005/api/modules
curl http://localhost:8005/api/skills
curl http://localhost:8005/api/tools
```

Run the mock LLM smoke test:

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}'
```

Run the structured mock smoke test:

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock","structured":true}'
```

## Stage 4 Files And Artifacts

Stage 4 adds local `.txt` and `.md` upload support plus run artifacts.
Uploaded files are stored with internal IDs instead of trusted filenames.

Create a run, upload a file, and attach it as an artifact:

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/files/$FILE_ID

ARTIFACT_ID=$(curl -s -X POST http://localhost:8005/api/runs/$RUN_ID/artifacts \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\",\"name\":\"README artifact\"}" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID/artifacts
curl http://localhost:8005/api/artifacts/$ARTIFACT_ID
```

## Stage 5A Demo Agent State Machine

Stage 5A routes `demo_agent` through a minimal observable state machine.
The existing run API stays compatible, and each node is recorded as a run step
and event.

Create a run and inspect the node trace:

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID
curl http://localhost:8005/api/runs/$RUN_ID/events
```

Expected node steps:

- `input_node`
- `skill_node`
- `tool_node`
- `final_node`

## Stage 5C Module Scaffold

Stage 5C adds a minimal module scaffold command for creating a new module from
the generic template.

Create a module:

```bash
python3 cli/scaffold_module.py sample_agent
```

Expected files:

- `modules/sample_agent/module.yaml`
- `modules/sample_agent/agent.yaml`
- `modules/sample_agent/services/sample_agent_service.py`
- `modules/sample_agent/prompts/system.md`
- `modules/sample_agent/skills/`
- `modules/sample_agent/evals/`
- `modules/sample_agent/README.md`

## Stop Infrastructure 停止基础设施

```bash
make down
```
