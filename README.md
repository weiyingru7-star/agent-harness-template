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

## V0.1.4 PostgreSQL Persistence 数据库持久化

V0.1.4 为核心运行数据补齐 PostgreSQL 最小持久化。现有 API 路径保持不变，开发期通过 SQLAlchemy `create_all` 初始化表。

已持久化的核心表：

- `tasks`
- `runs`
- `steps`
- `run_events`
- `files`
- `artifacts`
- `documents`
- `chunks`

启动 PostgreSQL：

```bash
make up
```

启动 API：

```bash
make dev-api
```

创建 Run 后验证数据库写入：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

DOCKER_CONFIG=$(pwd)/.docker docker compose exec postgres \
  psql -U agent_harness -d agent_harness \
  -c "select id, status from runs where id = '$RUN_ID';"
```

## V0.1.5 Acceptance Guard 测试与验收增强

V0.1.5 增强底座测试覆盖和业务词污染检查，不增加新业务功能。

完整验收命令：

```bash
make test-api
python3 scripts/check_business_terms.py
for f in schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done
```

更多说明：

- [V0.1.5 测试与验收增强](docs/v0.1.5-acceptance.md)

## V0.1.8 Module Registry 模块注册

V0.1.8 增强模块发现和 Agent 执行契约，不创建新的业务模块。

模块 manifest：

```text
modules/{module_name}/module.yaml
modules/{module_name}/agent.yaml
```

运行契约：

```python
def execute(input_text, context):
    ...
```

默认创建 Run 仍运行 `demo_agent`：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}'
```

也可以显式选择模块：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello","module_id":"demo_agent"}'
```

查看模块：

```bash
curl http://localhost:8005/api/modules
```

更多说明：

- [V0.1.8 Module Registry](docs/v0.1.8-acceptance.md)
- [Module Development](docs/module-development.md)
- [Agent Runtime](docs/agent-runtime.md)

## V0.2.1 Trace Runtime 可观察运行轨迹

V0.2.1 增强 Run 的可观察性。每次 Run 会生成 `trace_id`，每个 node step
会生成 `span_id`，事件会保留旧字段并增加 typed event 字段。

查询事件：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

查询 trace：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/trace
```

本阶段不实现 checkpoint、resume、retry，也不接外部 tracing 平台。

更多说明：

- [Trace Runtime](docs/trace-runtime.md)

## V0.2.2 Checkpoint Runtime 状态快照

V0.2.2 在每个 completed step 后保存一次 checkpoint。checkpoint 只保存
state snapshot，不实现 resume、retry 或 time travel。

查询 run checkpoints：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/checkpoints
```

查询单个 checkpoint：

```bash
curl http://localhost:8005/api/checkpoints/$CHECKPOINT_ID
```

更多说明：

- [Checkpoint Runtime](docs/checkpoint-runtime.md)

## V0.2.3 Failure / Retry Runtime 失败与手动重试

V0.2.3 让 Run 支持最小失败记录和手动 retry。retry 会重新执行整个 run，
生成新的 run，不覆盖旧 run，也不从 checkpoint 恢复。

触发测试失败输入：

```text
__fail__
```

手动 retry：

```bash
curl -X POST http://localhost:8005/api/runs/$RUN_ID/retry
```

更多说明：

- [Failure / Retry Runtime](docs/failure-retry-runtime.md)

## V0.2.4 Timeline API / 前端 Timeline 视图

V0.2.4 增加最小 Timeline API 和前端 Timeline 视图，把 run 的 steps、events、
spans、checkpoints 按时间顺序聚合为一条统一时间线，便于 debug 和轨迹回看。

查询 run 的 timeline：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/timeline
```

前端在 run 详情页（`apps/web/app/runs/[runId]/page.tsx`）直接渲染该时间线。

## V0.2.5 Eval Trajectory 最小评估

V0.2.5 增加最小 eval runner，用固定 eval cases 检查 demo_agent 的 run
status、output、events、steps、trace、checkpoints 和 timeline，防止后续改动破坏
Agent Runtime 轨迹。

运行 eval：

```bash
python3 scripts/run_evals.py
```

更多说明：

- [Eval Trajectory](docs/eval-trajectory.md)

## V0.3.0 Tool Call Contract 工具调用记录

V0.3.0 增加最小标准化 tool call 记录。`demo_agent` 在 `tool_node`
调用 mock echo tool 时会记录一条 `tool_call`，并写入 typed events：

- `tool.call.started`
- `tool.call.completed`

查询 run 的 tool calls：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

查询单条 tool call：

```bash
curl http://localhost:8005/api/tool-calls/$TOOL_CALL_ID
```

更多说明：

- [Tool Call Contract](docs/tool-call-contract.md)

## V0.3.1 Tool Args Schema / 参数校验最小版

V0.3.1 为 Tool 系统增加 `args_schema` 能力。每个 tool 可声明输入参数结构，
`ToolArgsValidator` 在 tool 执行前做最小校验。校验失败时不执行 tool，
记录 `tool.call.failed` event 和 `failed` 状态的 tool_call，但 run 仍然 `completed`。

demo_agent 触发方式：

- 正常输入：tool_call.status = `completed`
- `__invalid_tool_args__`：tool_call.status = `failed`，run 仍 `completed`

校验失败的 tool_call：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

更多说明：

- [Tool Args Schema](docs/tool-args-schema.md)

## V0.3.2 Tool Result Contract / 工具结果标准化最小版

V0.3.2 为 Tool 系统增加标准化 `ToolResult` Contract。每次工具执行后，
不管成功还是失败，都返回统一结构，便于 trace、timeline、eval 和后续
tool retry / timeout / permission / sandbox 扩展。

`mock_echo` 现返回标准 `ToolResult`。工具执行抛异常时被 `RunStore` 捕获，
记录 `failed` tool_call 和 `tool.call.failed` event。

demo_agent 触发方式：

- 正常输入：ToolResult(completed)，result 含 status/output/summary
- `__tool_exception__`：工具执行抛异常，捕获后 result(status=failed)

更多说明：

- [Tool Result Contract](docs/tool-result-contract.md)

## V0.3.3 Tool Timeout / 工具超时最小版

V0.3.3 为 Tool 系统增加最小 `timeout_ms` 能力。每个 tool 可声明超时时间，
工具执行超过限制时，记录 `ToolTimeoutError` 和 `tool.call.failed` event，
但 run 仍然 `completed`。

超时基于 `threading.Thread` 实现，纯标准库，无外部依赖。
`mock_echo` 默认 `timeout_ms=1000`。

demo_agent 触发方式：

- 正常输入：正常完成，`timeout_ms` 不生效
- `__slow_tool__`：模拟慢工具，触发 ToolTimeoutError

超时后的 tool_call：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

更多说明：

- [Tool Timeout](docs/tool-timeout.md)

## V0.3.4 Tool Retry / 工具重试最小版

V0.3.4 为 Tool 系统增加最小 retry 能力。工具调用失败时，可以按
`max_attempts` 重试。每次 attempt 都被记录到 ToolCall metadata
和 events 中。

`demo_agent` 触发方式：

- 正常输入：不触发 retry，`max_attempts=1` 行为不变
- `__flaky_tool__`：第一次执行失败、第二次执行成功（retry 成功路径）

更多说明：

- [Tool Retry](docs/tool-retry.md)

## V0.3.5 Tool Permission / 工具权限最小版

V0.3.5 为 Tool 系统增加最小权限校验能力。工具执行前检查权限，
拒绝时记录 `ToolPermissionDenied` 和 `tool.call.failed` event。

三个权限级别：
- `safe`：默认允许
- `restricted`：需要 context 显式允许
- `blocked`：永远拒绝

demo_agent 触发方式：

- 正常输入：safe 级别，正常执行
- `__restricted_tool__`：权限拒绝，tool 不执行
- `__blocked_tool__`：权限拒绝，tool 不执行

更多说明：

- [Tool Permission](docs/tool-permission.md)

## V0.3.6 Tool Sandbox / 安全执行最小版

V0.3.6 为 Tool 系统增加最小安全执行层。运行前检查该 tool
是否允许在当前执行模式下运行。违反 sandbox_policy 时，
记录 `ToolSandboxViolation` 和 `tool.call.failed` event。

执行顺序：
```
tool.call.started → permission check → sandbox check → args validation → execution
```

demo_agent 触发方式：

- `__sandbox_blocked__`：execution_mode 设为 disabled，被 sandbox 拒绝

更多说明：

- [Tool Sandbox](docs/tool-sandbox.md)

## V0.3.x Tool Runtime 总结

V0.3.0–V0.3.6 构建了一个完整的 Tool Runtime 执行栈，
从基础记录到安全执行共 7 层：

| 层级 | 版本 | 说明 | 文档 |
|---|---|---|---|
| 基础记录 | V0.3.0 | ToolCall 模型、事件记录、API 路由 | [Tool Call Contract](docs/tool-call-contract.md) |
| 参数校验 | V0.3.1 | args_schema 声明与 ToolArgsValidator | [Tool Args Schema](docs/tool-args-schema.md) |
| 结果标准化 | V0.3.2 | ToolResult 统一结构 | [Tool Result Contract](docs/tool-result-contract.md) |
| 超时控制 | V0.3.3 | timeout_ms + execute_with_timeout | [Tool Timeout](docs/tool-timeout.md) |
| 失败重试 | V0.3.4 | max_attempts + execute_with_retry | [Tool Retry](docs/tool-retry.md) |
| 权限校验 | V0.3.5 | permission_level + ToolPermissionChecker | [Tool Permission](docs/tool-permission.md) |
| 安全执行 | V0.3.6 | execution_mode + ToolSandboxChecker | [Tool Sandbox](docs/tool-sandbox.md) |

执行顺序：

```
tool.call.started → Permission → Sandbox → Args Validation
  → Timeout/Retry → Execution → ToolResult → tool.call.completed/failed
```

详细说明：[Tool Runtime 文档](docs/tool-runtime.md)

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

## V0.4.0 RAG Pipeline 增强

V0.4.0 强化了最小 RAG Pipeline，建立标准化 Document / Chunk / Citation /
Retrieval 数据契约。

增强内容：
- Document 模型：新增 `collection` / `title` / `source` / `content_type` 字段
- Chunk 模型：新增 `collection` / `char_count` / `token_count` 字段
- Citation 模型：新增 `title` / `source` / `quote` / `score` / `collection` 字段
- 新增 API：`GET /api/knowledge/documents/{document_id}`、`GET /api/knowledge/collections/{collection}/chunks`
- 新增 schema：citation.schema.json、retrieval-result.schema.json

关键词检索，不接 embedding 或向量库。

更多说明：

- [RAG Pipeline](docs/rag-pipeline.md)
- [RAG Contracts](docs/rag-contracts.md)

## V0.4.1 Chunking Strategy / 文档切分策略增强

V0.4.1 增强了 RAG Pipeline 的文档切分策略，支持可配置
`chunk_size`、`chunk_overlap`、按段落优先切分、超长段落 fallback。

增强内容：
- 新增 `ChunkingConfig`：`chunk_size` / `chunk_overlap` / `split_by` / `preserve_paragraphs` / `min_chunk_size`
- 段落优先切分（paragraph-first），超长段落自动 fallback 到固定字符切分
- 后处理模式 overlap（不传时行为与 V0.4.0 一致）
- Chunk 新增 `chunk_metadata`（start_char / end_char / split_strategy / overlap_with_previous / chunk_size / chunk_overlap）
- 存储于已有 `ChunkRecord.metadata_` JSON 列

ingest 时可通过 `chunking_config` 字段自定义切分参数，不传时使用默认策略。

更多说明：

- [RAG Chunking](docs/rag-chunking.md)

## V0.4.2 Direct Text Document Ingest / 直接文本创建文档

V0.4.2 新增 `POST /api/knowledge/documents` 入口，直接用文本创建
knowledge document，不依赖文件上传。

请求字段：`title`（必填）、`text`（必填）、`collection`、`source`、
`content_type`、`metadata`、`chunking_config`。

内部创建虚拟 FileRecord 满足外键约束，复用 V0.4.1 chunker 和已有检索链路。
可通过 `POST /api/knowledge/retrieve` 搜到直接创建的文档。

更多说明：

- [RAG Pipeline](docs/rag-pipeline.md)

## V0.4.3 RAG Eval 最小版

V0.4.3 新增最小 RAG 评估能力，通过结构化 eval case 验证 retrieve
是否命中预期 document / chunk / citation。

- 新增 `scripts/run_rag_evals.py`：独立 RAG eval runner
- 新增 `evals/rag_cases/`：RAG eval case 文件位置
- 新增 `schemas/rag-eval-case.schema.json`：RAG eval case 格式契约

运行方式：

```bash
python3 scripts/run_rag_evals.py
```

更多说明：

- [RAG Eval](docs/rag-eval.md)

## V0.4.4 Embedding Provider Interface / 嵌入层抽象最小版

V0.4.4 为 RAG Pipeline 增加 embedding provider 抽象层。当前只实现
`MockEmbeddingProvider`，不接真实 embedding API。

三个核心组件：
- `EmbeddingRequest` / `EmbeddingResult`：embedding 输入输出契约
- `EmbeddingProvider`：抽象基类，`MockEmbeddingProvider` 是唯一实现
- `EmbeddingRegistry`：按名称获取 provider

MockEmbeddingProvider 基于 MD5 + LCG 生成确定性伪嵌入（默认 8 维）。
通过测试套件验证 provider contract：`make test-api`（`test_rag_embeddings.py`）。

更多说明：

- [RAG Embeddings](docs/rag-embeddings.md)

## V0.4.5 Vector Store Interface / 向量存储接口最小版

V0.4.5 为 RAG Pipeline 增加 vector store 抽象层。当前只实现
`InMemoryVectorStore`，不接真实向量数据库。

四个核心组件：
- `VectorRecord` / `VectorSearchRequest` / `VectorSearchResult`：检索契约
- `VectorStore`（ABC）：upsert / search / delete / count
- `InMemoryVectorStore`：基于 dict + collection index 的内存实现
- cosine similarity（dot product on normalized vectors）

与 `MockEmbeddingProvider` 配合：embedding 向量可存入 InMemoryVectorStore 并检索。

更多说明：

- [RAG Vector Store](docs/rag-vector-store.md)

## Current Scope 当前范围

当前版本（V0.4.5）已完成：
- **V0.2.x Agent Runtime**：Trace / Span、Checkpoint、Failure / Retry、Timeline API 与前端视图、Eval Trajectory runner
- **V0.3.x Tool Runtime**：Tool Call Contract、Tool Args Schema、Tool Result Contract、Tool Timeout、Tool Retry、Tool Permission、Tool Sandbox Policy、文档收口
- **V0.4.0 RAG Pipeline**：增强 Document / Chunk / Citation / Retrieval Contract、新增文档详情与集合分块 API
- **V0.4.1 Chunking Strategy**：可配置 chunk_size / chunk_overlap、段落优先切分、超长段落 fallback、chunk_metadata
- **V0.4.2 Direct Text Document**：POST /api/knowledge/documents 直接文本创建
- **V0.4.3 RAG Eval**：独立 RAG eval runner + 结构化 eval case
- **V0.4.4 Embedding Provider**：EmbeddingRequest / Result / Provider contract、MockEmbeddingProvider、Registry
- **V0.4.5 Vector Store**：VectorRecord / Search contract、InMemoryVectorStore、cosine similarity

模板核心保持业务无关，具体业务逻辑应放在 `modules/{module_name}/` 内由使用者自行创建。详见 [Project Boundaries](PROJECT_BOUNDARIES.md)。

下一阶段规划：V0.4.x Embedding / Vector Store / Rerank。

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

V0.1.6 adds a minimal Provider Router and a unified provider interface. The mock
provider remains the default, and real providers are optional.

Provider environment variables:

```env
AI_PROVIDER=mock
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_TIMEOUT=30
```

`AI_PROVIDER` can be `mock` or `openai_compatible`. If a real provider is
selected without the required configuration, `/api/llm/smoke` returns a clear
400 error instead of affecting the default mock flow.

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

Check an unconfigured OpenAI-compatible provider:

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"openai_compatible"}'
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
