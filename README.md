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

## V0.4.6 Retrieval Mode Contract / 检索模式合同

V0.4.6 为 RAG retrieve 增加 `retrieval_mode` 合同，支持
keyword / vector / hybrid 三种模式：

- **keyword**（默认）：现有关键词计数检索，兼容 V0.4.0–0.4.5
- **vector**：MockEmbeddingProvider + InMemoryVectorStore 惰性索引
- **hybrid**：keyword + vector 去重合并

通过 `POST /api/knowledge/retrieve` 的可选字段 `retrieval_mode`
和 `collection` 控制。不传时走 keyword 路径，已有行为不变。

更多说明：

- [RAG Retrieval Modes](docs/rag-retrieval-modes.md)

## V0.4.x RAG Runtime 总结

V0.4.0–V0.4.6 构建了一个完整的 RAG Runtime 栈，共 7 个模块：

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| 数据合同 | V0.4.0 | Document / Chunk / Citation / RetrievalResult | [RAG Contracts](docs/rag-contracts.md) |
| 切分策略 | V0.4.1 | chunk_size / chunk_overlap / paragraph-fallback | [RAG Chunking](docs/rag-chunking.md) |
| 直接文本创建 | V0.4.2 | POST /api/knowledge/documents | [RAG Pipeline](docs/rag-pipeline.md) |
| 检索评估 | V0.4.3 | scripts/run_rag_evals.py | [RAG Eval](docs/rag-eval.md) |
| 嵌入层 | V0.4.4 | MockEmbeddingProvider + Registry | [RAG Embeddings](docs/rag-embeddings.md) |
| 向量存储 | V0.4.5 | InMemoryVectorStore + cosine similarity | [RAG Vector Store](docs/rag-vector-store.md) |
| 检索模式 | V0.4.6 | keyword / vector / hybrid + metadata | [RAG Retrieval Modes](docs/rag-retrieval-modes.md) |

详细说明：[RAG Runtime 文档](docs/rag-runtime.md)

## V0.5.0 Provider Runtime / 模型调用增强最小版

V0.5.0 系统化整理 LLM Provider 层，建立结构化合同和 fallback 策略。

三个核心组件：
- `ProviderRequest` / `ProviderResponse` / `ProviderError`：结构化调用合同
- `call_provider()`：统一调用入口，返回 ProviderResponse（含 latency_ms / usage）
- `call_provider_with_fallback()`：主 provider 失败时自动 fallback 到 mock

不改已有 `POST /api/llm/smoke`、`MockLLMProvider`、`ProviderRouter`。

更多说明：

- [Provider Runtime](docs/provider-runtime.md)
- [Provider Runtime Contracts](docs/provider-runtime-contracts.md)

## V0.5.1 Provider Smoke Response / smoke 响应合同对齐

V0.5.1 让 `POST /api/llm/smoke` 的响应对齐 `ProviderResponse` contract。

新增返回字段：`model` / `latency_ms` / `usage`（prompt_tokens /
completion_tokens / total_tokens）/ `finish_reason` / `metadata`
（provider_runtime_version / contract / mock 标记）。

路径不变、请求模型不变、错误处理不变。

更多说明：

- [Provider Runtime](docs/provider-runtime.md)

## V0.5.2 Provider Streaming Contract / 流式输出最小版

V0.5.2 为 Provider Runtime 增加最小 streaming contract。

新增内容：
- `ProviderStreamEvent`：stream_start / stream_delta / stream_end / stream_error
- `POST /api/llm/stream`：SSE 格式（text/event-stream）
- `MockLLMProvider.stream_text()`：单词级 delta 切分

更多说明：

- [Provider Streaming](docs/provider-streaming.md)

## V0.5.3 Provider Error / Fallback Path / 错误与回退最小版

V0.5.3 为 Provider Runtime 增加结构化错误和 fallback 最小路径。

新增内容：
- `MockFailingLLMProvider`：`id="mock_failing"`，所有调用抛异常
- `POST /api/llm/smoke` 新增可选 `fallback` 字段：primary 失败时自动回退
- fallback metadata 含 `fallback_used` / `fallback_from` / `fallback_to` / `fallback_reason` / `primary_error_type`
- stream fallback 列为 future 能力

更多说明：

- [Provider Errors](docs/provider-errors.md)

## V0.5.4 Provider Timeout / Retry / 超时与重试最小版

V0.5.4 为 Provider Runtime 增加 provider 调用级 timeout / retry 能力。

新增内容：
- `MockSlowLLMProvider`（`mock_slow`）：延迟响应，配合 `timeout_ms` 触发超时
- `MockFlakyLLMProvider`（`mock_flaky`）：首次失败，`max_attempts=2` 自动重试
- `call_provider_with_timeout_retry`：daemon thread 超时 + 简单 retry 循环
- `POST /api/llm/smoke` 支持 `timeout_ms` / `max_attempts` 参数
- retry 耗尽后自动走 V0.5.3 fallback 路径

更多说明：

- [Provider Timeout / Retry](docs/provider-timeout-retry.md)

## V0.5.5 Provider Config / Env Management / 配置管理最小版

V0.5.5 为 Provider Runtime 增加最小配置管理能力。

新增内容：
- `ProviderConfig` 模型：provider_name / model / timeout_ms / max_attempts / fallback_provider / api_key_configured
- `GET /api/llm/config`：安全暴露配置（API key 不出现，仅显示是否已配置）
- Settings 新增 `ai_max_attempts` / `ai_fallback_provider` / `ai_streaming_enabled`
- Smoke metadata 追加 `configured_provider` / `configured_model` / `config_source`

更多说明：

- [Provider Config](docs/provider-config.md)

## V0.5.6 OpenAI-Compatible Provider Adapter / 真实模型适配

V0.5.6 为 Provider Runtime 增加第一个真实 LLM provider adapter。
通过 `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` 配置即可接入
DeepSeek、智谱、Qwen、OpenRouter、硅基流动等兼容 OpenAI
Chat Completions 格式的模型。

增强内容：
- `_request_chat_completion` 提取 API 响应中的 usage / finish_reason / model
- HTTP 错误处理增强：解析 API 返回的错误消息
- secret 安全：API key 不在响应中暴露
- V0.5.3 fallback / V0.5.4 timeout/retry 完整兼容

更多说明：

- [OpenAI-Compatible Provider](docs/openai-compatible-provider.md)

## V0.5.x Provider Runtime 总结

V0.5.0–V0.5.6 构建了一个完整的 Provider Runtime 栈，共 7 个模块：

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| 基础合同 | V0.5.0 | ProviderRequest / Response / Error | [Provider Runtime](docs/provider-runtime.md) |
| 响应合同对齐 | V0.5.1 | smoke 返回对齐 ProviderResponse | [Provider Runtime](docs/provider-runtime.md) |
| 流式输出 | V0.5.2 | ProviderStreamEvent + SSE endpoint | [Provider Streaming](docs/provider-streaming.md) |
| 错误与回退 | V0.5.3 | MockFailingLLMProvider + fallback | [Provider Errors](docs/provider-errors.md) |
| 超时与重试 | V0.5.4 | MockSlow / MockFlaky + timeout / retry | [Provider Timeout Retry](docs/provider-timeout-retry.md) |
| 配置管理 | V0.5.5 | ProviderConfig + GET /api/llm/config | [Provider Config](docs/provider-config.md) |
| 真实模型适配 | V0.5.6 | OpenAI-compatible adapter | [OpenAI Provider](docs/openai-compatible-provider.md) |

详细说明：[Provider Runtime 文档](docs/provider-runtime.md)

## V0.6.0 Agent Template Contract / 智能体模板合同最小版

V0.6.0 定义业务无关的 Agent Template Contract，让一个 Agent 可以
通过 `agent.json` 声明它的基础信息、provider、tools、rag、workflow、
eval 配置。

新增内容：
- `AgentTemplate`：id / name / provider / tools / rag_collection / workflow / eval_cases
- `AgentTemplateRegistry`：从 `templates/agent-template/` 加载模板
- `GET /api/agent-templates` 和 `GET /api/agent-templates/{id}`

更多说明：

- [Agent Template Contract](docs/agent-template-contract.md)

## V0.6.1 Agent YAML Config Loader / 配置加载增强

V0.6.1 增强 agent 配置的字段能力，支持嵌套 provider / tools / rag /
workflow / eval 配置。

新增内容：
- `AgentConfig`：嵌套 ProviderRef / ToolsConfig / RagConfig / WorkflowConfig / EvalConfig
- 简写兼容：`"provider": "mock"` 和 `{"provider_name": "..."}` 均可
- `GET /api/agent-templates/{id}/config` 和 `GET /api/agent-templates/{id}/validate`

更多说明：

- [Agent YAML Config](docs/agent-yaml-config.md)

## V0.6.2 Agent Template Registry API / 注册表 API 增强

V0.6.2 增强 Agent Template Registry 的 API 响应结构，提供结构化
校验结果和摘要视图。

新增内容：
- `TemplateSummary`：列表视图含 `tools_count` / `rag_enabled` / `nodes_count` / `runtime_version`
- `ValidateResult`：结构化校验结果含 `template_id` / `valid` / `warnings` / `checked_at`
- `GET /api/agent-templates/{id}/validate` 返回 `ValidateResult`

更多说明：

- [Agent Template Registry API](docs/agent-template-registry-api.md)

## V0.6.3 Example Agent Template / 示例模板最小版

V0.6.3 新增业务无关的 example agent template `generic_agent`。
这是创建新 Agent 的参考起点，不是业务 Agent。

增强内容：
- 完整的 agent.json 示例（含 provider / tools / rag / workflow / eval / metadata）
- `templates/agent-template/README.md`：使用说明
- metadata 含 `author` / `repository` / `tags` / `purpose`

更多说明：

- [Example Agent Template](docs/example-agent-template.md)

## V0.7.0 Workflow Contract / 工作流合同最小版

V0.7.0 定义业务无关的 Workflow Contract，让 agent.yaml 中的 workflow
可以声明 nodes、edges、entrypoint、terminal nodes、node types。

新增内容：
- `WorkflowNode` / `WorkflowEdge` / `WorkflowCondition` 结构化模型
- `WorkflowValidator`：校验 entrypoint、node 唯一性、edge 引用、node type
- `terminal_nodes`、`node_types` 字段增强
- `validate API` 返回 workflow 校验结果
- 增强 `schemas/workflow.schema.json`

更多说明：

- [Workflow Contract](docs/workflow-contract.md)

## V0.7.1 Node / Edge / Condition Schema 增强

V0.7.1 增强 Workflow Contract 的 Node / Edge / Condition schema。

增强内容：
- `WorkflowNode`：新增 `description` / `inputs` / `outputs`
- `WorkflowEdge`：新增可选 `id`
- `WorkflowCondition`：新增 `on_success` / `on_failure`、`expected_value`
- Node type-specific config 校验：6 种 node 各有 allowed config key 白名单
- Validator 增强：condition type 校验、decision route 引用校验、rag retrieval_mode 校验

更多说明：

- [Workflow Contract](docs/workflow-contract.md)

## V0.7.2 Built-in Workflow Nodes / 内置工作流节点合同

V0.7.2 定义 6 种业务无关的 built-in workflow node contracts。

| 类型 | config key | 预期输出 |
|---|---|---|
| `input` | input_schema, default | payload |
| `provider` | provider_name, model, prompt_template, temperature | output, usage |
| `tool` | tool_name, args_template | result, status |
| `rag` | collection, retrieval_mode, query_template, limit | results, citations |
| `decision` | routes, default_route | selected_route |
| `final` | output_template | final_output |

`generic_agent` workflow 已更新为 dict 格式节点，展示完整 contract 用法。

更多说明：

- [Built-in Workflow Nodes](docs/workflow-built-in-nodes.md)

## V0.7.3 Workflow Validation / Eval / 校验与评估最小版

V0.7.3 为 workflow 增加结构化 validation result 和最小 eval 能力。

新增内容：
- `ValidationErrorItem`：code / message / path / severity 结构化错误
- 11 个 error codes（WORKFLOW_ENTRYPOINT_MISSING 等）
- `WorkflowValidationResult.error_items`：结构化错误列表
- `scripts/run_workflow_evals.py`：独立 workflow eval runner
- `evals/workflow_cases/valid_workflow.json`：合法 workflow 校验 case

更多说明：

- [Workflow Validation](docs/workflow-validation.md)

## V0.7.x Workflow Contract 总结

V0.7.0–V0.7.4 构建了 Workflow Contract 系统，共 4 个模块：

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| Workflow Contract | V0.7.0 | WorkflowNode / Edge / Condition / Validator | [Contract](docs/workflow-contract.md) |
| Schema 增强 | V0.7.1 | description / inputs / outputs / condition types | [Contract](docs/workflow-contract.md) |
| Built-in Nodes | V0.7.2 | 6 种 node types + contract validation | [Built-in Nodes](docs/workflow-built-in-nodes.md) |
| Validation / Eval | V0.7.3 | error codes + structured result + eval runner | [Validation](docs/workflow-validation.md) |

## Current Scope 当前范围

当前版本（V0.8.8）已完成：
- **V0.2.x Agent Runtime**：Trace / Span、Checkpoint、Failure / Retry、Timeline API 与前端视图、Eval Trajectory runner
- **V0.3.x Tool Runtime**：Tool Call Contract、Tool Args Schema、Tool Result Contract、Tool Timeout、Tool Retry、Tool Permission、Tool Sandbox Policy、文档收口
- **V0.4.x RAG Runtime**：数据合同、切分策略、直接文本创建、检索评估、嵌入层、向量存储、检索模式、文档收口
- **V0.5.x Provider Runtime**：ProviderRequest / Response / Error 合同、call_provider、fallback、smoke 响应合同对齐、streaming contract、error/fallback 路径、timeout/retry、config/env 管理、真实 OpenAI-compatible 适配
- **V0.6.x Agent Template**：AgentTemplate contract、嵌套配置、Registry API、TemplateSummary、ValidateResult、Example Agent Template
- **V0.7.x Workflow Contract**：Node/Edge/Condition schema、WorkflowValidator、校验规则、schema 增强、built-in node contracts、validation error codes、eval runner、文档收口
- **V0.7.6 Tool Pipeline**：从 RunStore 抽取 Tool Execution Pipeline 到独立 `tool_runtime/` 模块。纯重构——不改变 API 响应、Event 结构、Eval 或测试断言。详见 [Tool Execution Pipeline](docs/tool-execution-pipeline.md)。
- **V0.7.7 Provider Consolidation**：收口 `provider_runtime`（canonical layer）和 `ai_runtime`（legacy compatibility layer）的边界。新增收口文档，增加 deprecation 注释。不改变任何代码行为。详见 [Provider Runtime Consolidation](docs/provider-runtime-consolidation.md)。
- **V0.8.0 Policy / Guardrail Contract**：Policy / Guardrail / Rule / Condition 业务无关合同。新增 PolicyValidator（结构校验，不执行）、JSON Schema、AgentTemplate 集成、文档和测试。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.1 Policy Validation Evals**：独立 policy validation eval runner（`scripts/run_policy_evals.py`），7 个 eval case，补齐稳定 error codes。只验证 contract，不执行 policy。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.2 Guardrail Decision Contract**：GuardrailDecision / DecisionResult 业务无关合同，描述 policy / guardrail 标准化决策结果。新增结构校验、JSON Schema、eval case 和测试。只做 contract，不执行 policy。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.3 Guardrail Evaluation Context Contract**：EvaluationContext / EvaluationSubject 业务无关合同，描述 policy / guardrail 评估上下文结构。新增结构校验、JSON Schema、eval case。只做 contract，不执行 policy。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.4 Policy Dry-Run Evaluator**：PolicyDryRunEvaluator——根据 Policy/Guardrail/EvaluationContext 生成 DecisionResult。支持 always/match/route condition types，expression 安全拒绝（require_review + unsupported_expression）。6 个 dry_run eval case。不接 runtime，不拦截请求。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.5 Guardrail Runtime Integration Plan**：集成计划文档，设计 runtime 接入点（input/output/tool/rag/provider/workflow）、execution mode（disabled/validate_only/dry_run/enforce）、dry-run 与 enforcement 边界。不修改任何代码。详见 [Guardrail Runtime Integration Plan](docs/guardrail-runtime-integration-plan.md)。
- **V0.8.6 Input Guardrail Dry-Run Hook**：新增 `run_input_guardrail()` 在 `RunStore._create_run` 中插入 input dry-run hook。构造 input-scope EvaluationContext，调用 PolicyDryRunEvaluator，记录 `guardrail.dry_run.completed` event。纯 dry-run，不拦截请求，不改变 API response。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.7 Tool Guardrail Dry-Run Hook**：`run_tool_guardrail()` 在 `ToolExecutionPipeline._execute_tool` 中插入 tool dry-run hook。构造 tool-scope EvaluationContext，记录 `guardrail.dry_run.completed` event。纯 dry-run，不阻止 tool 执行，不改变 ToolCall contract。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。
- **V0.8.8 Provider / RAG Guardrail Dry-Run Helpers**：`run_provider_guardrail()` / `run_rag_guardrail()` dry-run helper 已实现。返回 DecisionResult dict。当前不做 runtime wiring——provider_runtime / rag runtime 没有 run_id / trace_id / event_repository 上下文。纯 helper，不接入运行链路。详见 [Policy Guardrail Contract](docs/policy-guardrail-contract.md)。

模板核心保持业务无关，具体业务逻辑应放在 `modules/{module_name}/` 内由使用者自行创建。详见 [Project Boundaries](PROJECT_BOUNDARIES.md)。

下一阶段规划：V0.8.9 Guardrail Runtime Docs Consolidation。

> 当前阶段 V0.8.8 为 Provider / RAG Guardrail Dry-Run Helpers。provider/rag
> runtime 当前没有 run_id / trace_id / event_repository 上下文，因此只做
> helper-level 实现和测试。未来 runtime 调用链携带 run context 时再接入
> event recording。

### Provider Layer 分层说明

`app/provider_runtime` 是 **canonical provider abstraction**（规范层），`app/ai_runtime` 是
**legacy compatibility layer**（兼容层）。新 provider 功能应添加到 `provider_runtime`，
不要新增对 `ai_runtime` 的依赖。详见 [Provider Runtime Consolidation](docs/provider-runtime-consolidation.md)。

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
