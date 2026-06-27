# Testing And Acceptance 测试与验收

本文档定义 Stage 1 的验收命令和常见问题排查方式。

## Stage 1 Acceptance Commands Stage 1 验收命令

安装后端依赖：

```bash
make install-api
```

安装前端依赖：

```bash
make install-web
```

安装全部依赖：

```bash
make install
```

启动 PostgreSQL 和 Redis：

```bash
make up
```

运行后端测试：

```bash
make test-api
```

启动后端：

```bash
make dev-api
```

启动前端：

```bash
make dev-web
```

停止 PostgreSQL 和 Redis：

```bash
make down
```

## Backend `/health` Acceptance 后端 `/health` 验收

后端运行后，请执行：

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

## Frontend Homepage Acceptance 前端首页验收

启动前端：

```bash
make dev-web
```

打开：

```text
http://localhost:3005
```

预期结果：

- 页面标题显示 `Agent Harness Template`
- 页面包含 frontend、backend、infrastructure 三个信息区块
- 后端运行时，API health 显示 `ok`
- 后端未运行时，API health 显示 `unavailable`

## Docker Compose Acceptance Docker Compose 验收

启动服务：

```bash
make up
```

检查服务：

```bash
DOCKER_CONFIG=$(pwd)/.docker docker compose ps
```

预期结果：

- `agent-harness-postgres` 正在运行并且 healthy
- `agent-harness-redis` 正在运行并且 healthy

默认本地端口：

- PostgreSQL：`localhost:15432`
- Redis：`localhost:16379`

## Pytest Acceptance Pytest 验收

运行：

```bash
make test-api
```

预期结果：

- `tests/test_health.py` 通过
- `tests/test_runs.py` 通过

## Stage 2 Run Acceptance Stage 2 Run 验收

启动后端：

```bash
make dev-api
```

创建 run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

预期结果：

- 返回 `201`
- `status` 为 `completed`
- `steps[0].name` 为 `demo_agent`
- `output` 包含 mock response

读取 run：

```bash
curl http://localhost:8005/api/runs/$RUN_ID
```

读取 events：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

预期 events 至少包含：

- `run.created`
- `run.started`
- `step.started`
- `step.completed`
- `run.completed`

## Stage 3 AI Runtime And Registry Acceptance Stage 3 验收

运行测试：

```bash
make test-api
```

预期结果：

- `tests/test_llm.py` 通过
- `tests/test_registries.py` 通过
- `tests/test_runs.py` 仍然通过

启动后端：

```bash
make dev-api
```

检查 modules：

```bash
curl http://localhost:8005/api/modules
```

检查 skills：

```bash
curl http://localhost:8005/api/skills
```

检查 tools：

```bash
curl http://localhost:8005/api/tools
```

检查 mock LLM smoke：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}'
```

预期结果：

- `provider` 为 `mock`
- `output` 包含 mock response
- 不需要真实外部模型配置

检查 structured output：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock","structured":true}'
```

预期结果：

- `structured_output.ok` 为 `true`

检查未配置的 OpenAI-compatible provider：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"openai_compatible"}'
```

预期结果：

- HTTP 400
- `detail` 说明 provider 缺少配置
- 不需要真实 API Key

V0.1.6 Provider 框架验收：

```bash
make test-api
python3 scripts/check_business_terms.py
```

再次创建 run：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}'
```

预期结果：

- run 正常完成
- output 显示 demo_agent 通过 mock skill 和 mock tool 生成结果

## Stage 4 Files And Artifacts Acceptance Stage 4 验收

运行测试：

```bash
make test-api
```

预期结果：

- `tests/test_files.py` 通过
- `tests/test_artifacts.py` 通过

启动后端：

```bash
make dev-api
```

创建 run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

上传 `.md` 文件：

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

读取 file：

```bash
curl http://localhost:8005/api/files/$FILE_ID
```

创建 artifact：

```bash
ARTIFACT_ID=$(curl -s -X POST http://localhost:8005/api/runs/$RUN_ID/artifacts \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\",\"name\":\"README artifact\"}" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

读取 run artifacts：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/artifacts
```

读取 artifact：

```bash
curl http://localhost:8005/api/artifacts/$ARTIFACT_ID
```

预期结果：

- 只接受 `.txt` 和 `.md`
- artifact 与 run 关联
- artifact text 来自上传文件的最小文本提取

## Stage 5A State Machine Acceptance Stage 5A 验收

运行测试：

```bash
make test-api
```

预期结果：

- `tests/test_state_machine.py` 通过
- `tests/test_runs.py` 仍然通过

启动后端：

```bash
make dev-api
```

创建 run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

读取 run：

```bash
curl http://localhost:8005/api/runs/$RUN_ID
```

预期 steps 包含：

- `input_node`
- `skill_node`
- `tool_node`
- `final_node`

读取 events：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

预期 events 包含每个节点的：

- `node.started`
- `node.completed`

## Stage 5C Module Scaffold Acceptance Stage 5C 验收

创建模块：

```bash
python3 cli/scaffold_module.py sample_agent
```

预期生成：

- `modules/sample_agent/module.yaml`
- `modules/sample_agent/agent.yaml`
- `modules/sample_agent/services/sample_agent_service.py`
- `modules/sample_agent/prompts/system.md`
- `modules/sample_agent/skills/`
- `modules/sample_agent/evals/`
- `modules/sample_agent/README.md`

重复创建同名模块：

```bash
python3 cli/scaffold_module.py sample_agent
```

预期结果：

- 命令失败
- 不覆盖已有 `modules/sample_agent`

## V0.1.4 PostgreSQL Persistence Acceptance V0.1.4 验收

运行后端测试：

```bash
make test-api
```

预期结果：

- 现有 API 测试通过
- `tests/test_persistence.py` 通过
- Run、Step、Event、File、Artifact、Document、Chunk 可以写入并读取

启动 PostgreSQL 和 Redis：

```bash
make up
```

启动后端：

```bash
make dev-api
```

创建 run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

查询 API：

```bash
curl http://localhost:8005/api/runs/$RUN_ID
curl http://localhost:8005/api/runs/$RUN_ID/events
```

查询 PostgreSQL：

```bash
DOCKER_CONFIG=$(pwd)/.docker docker compose exec postgres \
  psql -U agent_harness -d agent_harness \
  -c "select id, status from runs where id = '$RUN_ID';"
```

预期结果：

- API 返回格式保持兼容
- `runs` 表中存在对应 `RUN_ID`
- `steps` 和 `run_events` 表中存在该 run 的执行记录

## V0.1.5 Acceptance Guard V0.1.5 测试增强

运行完整后端测试：

```bash
make test-api
```

预期结果：

- Run persistence 测试通过
- File / Artifact persistence 测试通过
- Knowledge persistence 测试通过
- Schema validation 测试通过
- Scaffold 测试通过

运行业务词污染检查：

```bash
python3 scripts/check_business_terms.py
```

预期结果：

- 底座核心目录无业务词污染
- 禁止词清单和规则说明中的业务词允许出现

校验 schema JSON：

```bash
for f in schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done
```

完整验收：

```bash
make test-api
python3 scripts/check_business_terms.py
for f in schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done
cd apps/web && npm run build
```

## V0.1.8 Module Registry V0.1.8 模块注册验收

查看模块：

```bash
curl http://localhost:8005/api/modules
```

默认创建 Run：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}'
```

显式使用 demo module：

```bash
curl -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello","module_id":"demo_agent"}'
```

完整验收：

```bash
make test-api
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

## V0.2.1 Trace Runtime V0.2.1 可观察运行轨迹验收

创建 Run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello trace"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

检查旧事件接口兼容：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

预期结果：

- 返回 list。
- 每个事件仍包含 `type`、`message`、`created_at`。
- 新增 `event_type`、`trace_id`、`sequence` 等字段。

检查 trace：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/trace
```

预期结果：

- 返回 `run_id`。
- 返回 `trace_id`。
- `spans` 包含 input / skill / tool / final 四个 node。
- `events` 按 `sequence` 排序。

完整验收：

```bash
make test-api
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
for f in schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done
git diff --check
```

开发期数据库说明：

- 新测试库或新开发库会自动创建 V0.2.1 字段。
- 已存在的本地 PostgreSQL 表不会被 `create_all` 自动修改。
- 如旧开发库报字段不存在，请先备份需要的数据，再手动补字段或重建本地开发数据库。

## V0.2.2 Checkpoint Runtime V0.2.2 状态快照验收

创建 Run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello checkpoint"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

检查 checkpoints：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/checkpoints
```

预期结果：

- 返回 4 条 checkpoint。
- `checkpoint_index` 为 1、2、3、4。
- metadata 中的 step name 对应 input / skill / tool / final。

读取单个 checkpoint：

```bash
CHECKPOINT_ID=$(curl -s http://localhost:8005/api/runs/$RUN_ID/checkpoints \
  | python3 -c "import json, sys; print(json.load(sys.stdin)[0]['id'])")

curl http://localhost:8005/api/checkpoints/$CHECKPOINT_ID
```

兼容性检查：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
curl http://localhost:8005/api/runs/$RUN_ID/trace
```

## V0.2.3 Failure / Retry Runtime V0.2.3 失败与重试验收

创建失败 Run：

```bash
FAILED_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello __fail__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

检查失败记录：

```bash
curl http://localhost:8005/api/runs/$FAILED_RUN_ID
curl http://localhost:8005/api/runs/$FAILED_RUN_ID/events
curl http://localhost:8005/api/runs/$FAILED_RUN_ID/trace
curl http://localhost:8005/api/runs/$FAILED_RUN_ID/checkpoints
```

预期结果：

- run status 为 `failed`。
- failed step 为 `skill_node`。
- failed step 包含 `error_type` / `error_message`。
- events 包含 `step.failed` / `run.failed`。
- trace 和 checkpoints 仍可查询。

手动 retry：

```bash
RETRY_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs/$FAILED_RUN_ID/retry \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RETRY_RUN_ID
curl http://localhost:8005/api/runs/$RETRY_RUN_ID/events
```

预期结果：

- retry 生成新的 run id。
- retry run metadata 包含 `retry_of_run_id`。
- events 包含 `run.retry_started`。

## V0.7.6 Tool Pipeline Refactor Acceptance V0.7.6 重构验收

V0.7.6 是纯重构：将 tool execution pipeline 从 RunStore 抽取到独立
`apps/api/app/tool_runtime/` 模块。不改变任何 API 行为、Event 结构、
Tool Runtime 合同或测试断言。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 266 passed）
make test-api

# Agent trajectory eval（预期 8 passed）
python3 scripts/run_evals.py

# RAG eval（预期 2 passed）
python3 scripts/run_rag_evals.py

# Workflow eval（预期 1 passed）
python3 scripts/run_workflow_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### 行为不变性检查

所有以下行为与重构前完全一致：

- `POST /api/runs` 响应结构不变
- `GET /api/runs/{id}` 响应结构不变
- `GET /api/runs/{id}/tool-calls` 响应结构不变
- `GET /api/tool-calls/{id}` 响应结构不变
- tool.call.started / completed / failed / retry_scheduled event 类型和 metadata 不变
- ToolCall 模型字段不变
- Sequence 顺序不变
- Trace / Checkpoint / Timeline 语义不变
- Tool Runtime contract（Permission / Sandbox / Args / Retry / Timeout）不变

### 文档参考

- [Tool Execution Pipeline](docs/tool-execution-pipeline.md)

## V0.7.7 Provider Runtime Consolidation Acceptance V0.7.7 Provider 运行时收口验收

V0.7.7 只做 provider 边界收口和文档整理，不改变任何代码行为。

### 验收确认项

- `provider_runtime` 被正式确认为 canonical provider abstraction
- `ai_runtime` 被正式标记为 legacy compatibility layer，暂不删除
- 新 provider 功能应添加在 `provider_runtime`，不新增对 `ai_runtime` 的依赖
- 所有已有 provider 行为不变
- 所有已有 API response 不变
- 所有已有 tests 不变

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 270 passed）
make test-api

# Agent trajectory eval（预期 8 passed）
python3 scripts/run_evals.py

# RAG eval（预期 2 passed）
python3 scripts/run_rag_evals.py

# Workflow eval（预期 1 passed）
python3 scripts/run_workflow_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### Provider Test 说明

- **CI 使用 mock provider**：所有 CI 测试和 eval runner 默认使用 `AI_PROVIDER=mock`
- **真实 provider smoke test**：需要本地手动配置 `.env` 后运行 `POST /api/llm/smoke`
  （如 `AI_PROVIDER=openai_compatible` + `AI_API_KEY` 等）
- **真实 provider 调用不进入默认 CI**：`.env` 文件不得提交

### 文档参考

- [Provider Runtime Consolidation](docs/provider-runtime-consolidation.md)

## V0.8.0 Policy / Guardrail Contract Acceptance V0.8.0 策略与护栏合同验收

V0.8.0 定义业务无关的 Policy / Guardrail Contract。只做合同定义、
结构校验、JSON Schema、文档和测试。**不执行 policy，不拦截真实请求**。

### Contract 合同

| 模型 | 说明 |
|---|---|
| `Policy` | 策略合同：id / name / version / scope / rules / default_action |
| `Guardrail` | 护栏合同：id / name / type / policy_ref / action |
| `Rule` | 规则合同：id / condition / action / severity / message |
| `Condition` | 条件合同：type(always/expression/match/route) |

scope 枚举：`input`, `output`, `tool`, `rag`, `provider`, `workflow`
action 枚举：`allow`, `block`, `warn`, `require_review`

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 289 passed）
make test-api

# Agent trajectory eval（预期 8 passed）
python3 scripts/run_evals.py

# RAG eval（预期 2 passed）
python3 scripts/run_rag_evals.py

# Workflow eval（预期 1 passed）
python3 scripts/run_workflow_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### 行为不变性检查

所有以下行为与重构前完全一致：

- PolicyValidator **只做结构校验，不执行 condition**
- generic_agent 空 policies/guardrails 时 validate 仍为 valid=true
- AgentTemplate validate API response 结构不变（新增 policy_error_items 在 metadata 中）
- 所有已有 API 路径和响应不变
- 所有已有 tests 不变
- 所有已有 eval 不变
- 没有新增 API endpoint

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## Common Errors 常见错误排查

### `python: command not found`

使用 `python3`。Makefile 默认使用：

```bash
PYTHON=python3
```

如需覆盖：

```bash
make install-api PYTHON=/path/to/python
```

### `externally-managed-environment`

不要把依赖安装到系统 Python。Makefile 会创建：

```text
apps/api/.venv
```

请运行：

```bash
make install-api
```

### `pytest: command not found`

说明后端依赖尚未安装。

请运行：

```bash
make install-api
make test-api
```

### npm cache permission error

Makefile 使用项目内 npm cache：

```text
.npm-cache
```

请运行：

```bash
make install-web
```

### Docker credential helper error

Makefile 会准备项目内 Docker config：

```text
.docker
```

请运行：

```bash
make up
```

### Port already allocated

Stage 1 默认使用较少冲突的本地端口：

- PostgreSQL 使用宿主机端口 `15432`
- Redis 使用宿主机端口 `16379`

如果端口仍被占用，请在 `.env` 中调整 `POSTGRES_PORT` 或 `REDIS_PORT`。

### Frontend shows API `unavailable`

说明前端没有连上后端。请先启动后端：

```bash
make dev-api
```

然后刷新：

```text
http://localhost:3005
```

## V0.2.5 Eval Trajectory Acceptance V0.2.5 轨迹评估验收

运行最小 eval runner：

```bash
python3 scripts/run_evals.py
```

预期结果：

- `demo_agent_success` 通过。
- `demo_agent_failure` 通过。
- summary 显示全部 eval case passed。

完整回归验收：

```bash
python3 scripts/run_evals.py
make test-api
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

eval runner 会检查：

- run status。
- output 是否包含预期文本。
- events 是否包含预期 event type。
- steps 是否包含预期 step name。
- trace spans 数量。
- checkpoints 数量。
- timeline items 数量。

## V0.3.0 Tool Call Contract Acceptance V0.3.0 工具调用记录验收

创建 run：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello tool call"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
```

读取 run tool calls：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

读取单条 tool call：

```bash
TOOL_CALL_ID=$(curl -s http://localhost:8005/api/runs/$RUN_ID/tool-calls \
  | python3 -c "import json, sys; print(json.load(sys.stdin)[0]['id'])")

curl http://localhost:8005/api/tool-calls/$TOOL_CALL_ID
```

预期结果：

- 返回一条 `mock_echo` tool call。
- events 包含 `tool.call.started` 和 `tool.call.completed`。
- timeline 中 `tool_node` item 包含 `tool_call_id`。

完整回归：

```bash
python3 scripts/run_evals.py
make test-api
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

## V0.3.x Tool Runtime Acceptance V0.3.x 工具运行时验收

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 96 passed）
make test-api

# Eval runner（预期 8 passed）
python3 scripts/run_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web
```

### Normal Tool Call 正常工具调用

创建 run 并检查正常路径：

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID/tool-calls | python3 -m json.tool
```

预期结果：
- tool_call.status = `completed`
- tool_call.result.status = `completed`
- tool_call.result.output 以 `Mock tool echo` 开头
- events 包含 `tool.call.started` 和 `tool.call.completed`

### Invalid Args 参数校验失败

```bash
FAILED_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __invalid_tool_args__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$FAILED_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, error_type={tc[\"error_type\"]}')
"
```

预期结果：`status=failed, error_type=ToolArgsValidationError`

### Tool Exception 工具异常

```bash
EXC_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __tool_exception__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$EXC_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, error_type={tc[\"error_type\"]}')
"
```

预期结果：`status=failed, error_type=ToolExecutionError`

### Tool Timeout 工具超时

```bash
TIMEOUT_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __slow_tool__ timeout"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$TIMEOUT_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, error_type={tc[\"error_type\"]}, duration_ms={tc[\"duration_ms\"]}')
"
```

预期结果：`status=failed, error_type=ToolTimeoutError, duration_ms≥900`

### Flaky Tool Retry 工具重试

```bash
RETRY_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __flaky_tool__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RETRY_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, retry_count={tc[\"metadata\"][\"retry_count\"]}, attempts={len(tc[\"metadata\"][\"attempts\"])}')
"
```

预期结果：`status=completed, retry_count=1, attempts=2`

### Permission Denied 权限拒绝

```bash
PERM_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __restricted_tool__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$PERM_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, error_type={tc[\"error_type\"]}')
"
```

预期结果：`status=failed, error_type=ToolPermissionDenied`

### Sandbox Blocked 沙箱拒绝

```bash
SBOX_RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"trigger __sandbox_blocked__"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$SBOX_RUN_ID/tool-calls | python3 -c "
import json, sys
tc = json.load(sys.stdin)[0]
print(f'status={tc[\"status\"]}, error_type={tc[\"error_type\"]}')
"
```

预期结果：`status=failed, error_type=ToolSandboxViolation`

### Compatibility Check 兼容性检查

所有 8 条路径的 events、trace、checkpoints、timeline 均可查询：

```bash
# 以正常路径为例
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"compatibility check"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID/events
curl http://localhost:8005/api/runs/$RUN_ID/trace
curl http://localhost:8005/api/runs/$RUN_ID/checkpoints
curl http://localhost:8005/api/runs/$RUN_ID/timeline
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

### 文档参考

- [Tool Runtime 文档](docs/tool-runtime.md)
- [Tool Runtime Architecture](docs/tool-runtime-architecture.md)
- [Tool Runtime Errors](docs/tool-runtime-errors.md)
- [Tool Runtime Eval](docs/tool-runtime-eval.md)

## V0.4.0 RAG Pipeline Acceptance V0.4.0 RAG Pipeline 验收

### API 清单

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/knowledge/ingest` | **文档创建入口**（需要先上传文件获得 file_id） |
| GET | `/api/knowledge/documents` | 列出所有文档 |
| GET | `/api/knowledge/documents/{document_id}` | 查询单文档详情 |
| GET | `/api/knowledge/collections/{collection}/chunks` | 按集合查询分块 |
| POST | `/api/knowledge/retrieve` | 检索 chunks |

注意：`POST /api/knowledge/documents` 当前不存在，文档创建须通过 `POST /api/knowledge/ingest`。

### Unified Commands 统一命令

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
npm run build --prefix apps/web
```

### Ingest And Retrieve 文档导入与检索

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")

INGEST=$(curl -s -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}")
echo "$INGEST" | python3 -c "import json,sys;d=json.load(sys.stdin);print('doc id:',d['document']['id'],'chunks:',len(d['chunks']))"
```

预期结果：返回 document.id 和 chunks 列表。

### Enhanced Fields 增强字段

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
DOC_ID=$(curl -s -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}" | python3 -c "import json,sys;print(json.load(sys.stdin)['document']['id'])")

# Enhanced document fields
curl -s http://localhost:8005/api/knowledge/documents/$DOC_ID | python3 -c "
import json,sys;d=json.load(sys.stdin)
print('collection:',d.get('collection'),'title:',d.get('title'),'source:',d.get('source'))
"

# Enhanced chunk fields
curl -s http://localhost:8005/api/knowledge/collections/default/chunks | python3 -c "
import json,sys;c=json.load(sys.stdin)[0]
print('char_count:',c.get('char_count'),'token_count:',c.get('token_count'))
"

# Enhanced citation fields
QUERY=$(curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"Agent","limit":3}')
echo "$QUERY" | python3 -c "
import json,sys;r=json.load(sys.stdin)['results'][0]['citation']
print('title:',r.get('title'),'score:',r.get('score'),'quote:',r.get('quote')[:30] if r.get('quote') else None)
"
```

预期结果：
- document 包含 `collection`、`title`、`source`
- chunk 包含 `char_count`、`token_count`
- citation 包含 `title`、`score`、`quote`

### Document Detail API 文档详情

```bash
curl http://localhost:8005/api/knowledge/documents/doc_missing
```

预期结果：HTTP 404。

### Collection Chunks API 集合分块

```bash
curl http://localhost:8005/api/knowledge/collections/default/chunks | python3 -c "
import json,sys;chunks=json.load(sys.stdin)
print(f'{len(chunks)} chunks found')
if chunks: print('first chunk token_count:',chunks[0].get('token_count'))
"
```

### Compatibility 兼容性

```bash
make test-api
python3 scripts/run_evals.py
```

### 文档参考

- [RAG Pipeline](docs/rag-pipeline.md)
- [RAG Contracts](docs/rag-contracts.md)

## V0.4.1 Chunking Strategy Acceptance V0.4.1 切分策略验收

### Default Chunking 默认策略（兼容 V0.4.0）

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
curl -s -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}" | python3 -c "
import json,sys;d=json.load(sys.stdin)
print(f'chunks: {len(d[\"chunks\"])}, first: {d[\"chunks\"][0].get(\"chunk_metadata\",{})}')
"
```

预期结果：chunks 数 > 0，chunk_metadata 字段完整。

### Custom Chunking 自定义策略

使用 `chunking_config` 设置 chunk_size=100，chunk_overlap=20：

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
curl -s -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\",\"chunking_config\":{\"chunk_size\":100,\"chunk_overlap\":20}}" \
  | python3 -c "
import json,sys;d=json.load(sys.stdin)
print(f'chunks: {len(d[\"chunks\"])}')
if len(d['chunks']) > 1:
    print(f'overlap: {d[\"chunks\"][1][\"chunk_metadata\"][\"overlap_with_previous\"]}')
"
```

预期结果：
- 不传 chunking_config 时使用默认策略（500，0 overlap）
- 传 chunking_config 时按配置切分
- chunk_metadata 包含 start_char / end_char / split_strategy / overlap_with_previous / chunk_size / chunk_overlap

### Compatibility 兼容性

```bash
make test-api
python3 scripts/run_evals.py
```

### 文档参考

- [RAG Chunking](docs/rag-chunking.md)

## V0.4.2 Direct Text Document Ingest Acceptance V0.4.2 直接文本创建验收

### API 清单

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/knowledge/documents` | 直接从文本创建文档（不依赖文件上传） |

### Create Document 创建文档

```bash
curl -s -X POST http://localhost:8005/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Hello World","text":"This is a direct text document created without file upload."}' \
  | python3 -c "
import json,sys;d=json.load(sys.stdin)
print(f'doc_id={d[\"document\"][\"id\"]} title={d[\"document\"][\"title\"]} source={d[\"document\"][\"source\"]} chunks={len(d[\"chunks\"])}')
"
```

预期结果：返回 document 和 chunks，source="direct"。

### With ChunkingConfig 自定义切分

```bash
curl -s -X POST http://localhost:8005/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Long Document","text":"Para one.\n\nPara two.\n\nPara three.","chunking_config":{"chunk_size":30,"chunk_overlap":5}}' \
  | python3 -c "
import json,sys;d=json.load(sys.stdin)
print(f'chunks: {len(d[\"chunks\"])}')
if d['chunks']:
    print(f'metadata: {d[\"chunks\"][0].get(\"chunk_metadata\",{})}')
"
```

预期结果：chunks > 1，chunk_metadata 含 chunk_size=30。

### Validation 校验

```bash
# Missing text
curl -s -X POST http://localhost:8005/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"No Text"}' -o /dev/null -w '%{http_code}'
```

预期结果：422。

### Retrieval 检索

```bash
curl -s -X POST http://localhost:8005/api/knowledge/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Findable","text":"This direct text document contains unique keyword for retrieval."}' \
  > /dev/null

curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"unique keyword","limit":3}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)['results']
for res in r:
    c=res['citation']
    print(f'doc={c[\"title\"]} score={c[\"score\"]} source={c[\"source\"]} quote={c[\"quote\"][:40]}')
"
```

预期结果：能检索到 direct text 创建的文档，citation 含完整字段。

### File Ingest 不受影响

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
curl -s -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}" | python3 -c "import json,sys;d=json.load(sys.stdin);print('ingest ok:',d['document']['id'])"
```

预期结果：原有 file→ingest 链路正常运行。

### Compatibility 兼容性

```bash
make test-api
python3 scripts/run_evals.py
```

### 文档参考

- [RAG Pipeline](docs/rag-pipeline.md)


## V0.4.3 RAG Eval Acceptance V0.4.3 检索评估验收

### Run RAG Eval 运行 RAG 评估

```bash
python3 scripts/run_rag_evals.py
```

预期结果：

```
PASS retrieve_checkpoint_title
PASS retrieve_tool_call_title
Summary: 2 passed, 0 failed, 2 total
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [RAG Eval](docs/rag-eval.md)

## V0.4.4 Embedding Provider Interface Acceptance V0.4.4 嵌入层验收

V0.4.4 不暴露 embedding HTTP API。EmbeddingProvider contract 通过测试验收。

### 功能验证

- MockEmbeddingProvider 返回 8 维向量
- 相同输入返回相同 embedding
- 不同输入返回不同 embedding
- 批量 input 可用
- 可通过 Registry 获取 provider

验证命令：

```bash
make test-api
```

（`tests/test_rag_embeddings.py` 覆盖上述全部功能。）

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [RAG Embeddings](docs/rag-embeddings.md)

## V0.4.5 Vector Store Interface Acceptance V0.4.5 向量存储接口验收

V0.4.5 不暴露 HTTP API。VectorStore contract 通过测试验收。

### 功能验证

- InMemoryVectorStore 支持 upsert / search / delete / count
- collection 过滤生效
- reference 按 cosine similarity（dot product）排序
- 相同 vector score ≈ 1.0，正交 vector score ≈ 0.0
- MockEmbeddingProvider 向量可进出 vector store
- 批量操作正确

验证命令：

```bash
make test-api
```

（`tests/test_rag_vector_store.py` 覆盖上述全部功能，12 条测试。）

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [RAG Vector Store](docs/rag-vector-store.md)

## V0.4.6 Retrieval Mode Contract Acceptance V0.4.6 检索模式验收

V0.4.6 新增 `retrieval_mode` 字段，支持 `"keyword"` / `"vector"` / `"hybrid"`。

### API 使用

```bash
# keyword（默认）
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"checkpoints","retrieval_mode":"keyword"}' \
  | python3 -c "import json,sys;r=json.load(sys.stdin);print('results:',len(r['results']),'mode:',r['metadata']['retrieval_mode'])"
```

```bash
# vector
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"state snapshots","retrieval_mode":"vector"}' \
  | python3 -c "import json,sys;r=json.load(sys.stdin)['results'][0];print('score:',r['score'],'score_type:',r['score_type'],'mode:',r['retrieval_mode'])"
```

```bash
# hybrid
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"execution","retrieval_mode":"hybrid"}' \
  | python3 -c "import json,sys;r=json.load(sys.stdin);print('results:',len(r['results']),'mode:',r['metadata']['retrieval_mode'])"
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [RAG Retrieval Modes](docs/rag-retrieval-modes.md)

## V0.4.x RAG Runtime Acceptance V0.4.x 运行时验收

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试
make test-api

# Agent trajectory eval
python3 scripts/run_evals.py

# RAG eval
python3 scripts/run_rag_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web
```

### Keyword Retrieval 关键词检索

```bash
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"checkpoints","retrieval_mode":"keyword"}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('results:',len(r['results']),'metadata:',r.get('metadata'))
"
```

预期结果：results > 0，`metadata.retrieval_mode = "keyword"`

### Vector Retrieval 向量检索

```bash
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"checkpoints","retrieval_mode":"vector","collection":"default"}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('results:',len(r['results']),'metadata:',r.get('metadata'))
"
```

预期结果：results > 0，`metadata.retrieval_mode = "vector"`

### Hybrid Retrieval 混合检索

```bash
curl -s -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"checkpoints","retrieval_mode":"hybrid"}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('results:',len(r['results']),'metadata:',r.get('metadata'))
"
```

### Compatibility 兼容性

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```

### 文档参考

- [RAG Runtime 文档](docs/rag-runtime.md)
- [RAG Runtime Architecture](docs/rag-runtime-architecture.md)
- [RAG Runtime Contracts](docs/rag-runtime-contracts.md)
- [RAG Runtime Eval](docs/rag-runtime-eval.md)

## V0.5.0 Provider Runtime Acceptance V0.5.0 模型调用验收

### Smoke API 兼容性

```bash
# keyword mode — unchanged
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello"}' \
  | python3 -c "import json,sys;r=json.load(sys.stdin);print('provider:',r['provider'],'model:',r['model'],'latency_ms:',r['latency_ms'],'output:',r['output'][:30])"
```

预期结果：`provider: mock model: mock latency_ms: ... output: Mock LLM response for: hello`

### call_provider

ProviderResponse 包含 provider / model / latency_ms / usage：

```bash
# Through test suite
make test-api
```

（`tests/test_provider_runtime.py` 覆盖 call_provider / fallback / metadata。）

### Fallback

当 primary provider 未知时自动 fallback 到 mock，metadata 记录 fallback 信息。

## V0.5.2 Provider Streaming Acceptance V0.5.2 流式输出验收

### Stream Endpoint

```bash
curl -s -N -X POST http://localhost:8005/api/llm/stream \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}' 2>&1 | head -10
```

预期结果：SSE 格式，`data: {"event_type":"stream_start"..."}...data: {"event_type":"stream_end"...}`。

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Provider Runtime](docs/provider-runtime.md)
- [Provider Runtime Contracts](docs/provider-runtime-contracts.md)

## V0.5.3 Provider Error / Fallback Acceptance V0.5.3 错误与回退验收

### Fallback smoke

`POST /api/llm/smoke` 默认启用 fallback。primary provider 失败时自动
fallback 到 `"mock"` provider，HTTP status 200。

```bash
# mock_failing 自动 fallback 到 mock（不传 fallback 也可以）
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_failing"}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'fallback:',r['metadata'].get('fallback_used'),'error:',r['metadata'].get('primary_error_type'))
"

# openai_compatible 未配置时自动 fallback 到 mock
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"openai_compatible"}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'fallback:',r['metadata'].get('fallback_used'),'error:',r['metadata'].get('primary_error_type'))
"
```

预期结果：provider=mock，fallback_used=true，metadata 含 fallback_from / fallback_to / fallback_reason / primary_error_type。

### Compatibility 兼容性

不传 `fallback` 时默认 fallback 到 `"mock"`。正常 provider（如 `"mock"`）
不受影响（无错误时不触发 fallback）。

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Provider Errors](docs/provider-errors.md)

## V0.5.4 Provider Timeout / Retry Acceptance V0.5.4 超时与重试验收

### Flaky Provider Retry

```bash
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_flaky","max_attempts":2}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'retried:',r['metadata'].get('retried'),'retry_count:',r['metadata'].get('retry_count'))
"
```

预期结果：provider=mock_flaky，retried=true，retry_count=1，attempts 含 2 条记录。

### Timeout + Fallback

```bash
# slow provider 超时后自动 fallback 到 mock
# (mock_slow 默认延迟 3000ms，timeout_ms=100 触发超时)
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_slow","timeout_ms":100}' \
  | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'fallback:',r['metadata'].get('fallback_used'))
"
```

预期结果：provider=mock，fallback_used=true（超时后 fallback 到 mock）。

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Provider Timeout / Retry](docs/provider-timeout-retry.md)

## V0.5.5 Provider Config / Env Management Acceptance V0.5.5 配置管理验收

### Config Endpoint

```bash
curl -s http://localhost:8005/api/llm/config | python3 -m json.tool
```

预期结果：返回 JSON，含 provider_name / model / timeout_ms / max_attempts / fallback_provider / api_key_configured / streaming_enabled。不包含 `api_key` 或 `AI_API_KEY`。

### Smoke Metadata

`POST /api/llm/smoke` 响应的 metadata 包含 `configured_provider` / `configured_model` / `config_source`。

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Provider Config](docs/provider-config.md)

## V0.5.6 OpenAI-Compatible Provider Adapter Acceptance V0.5.6 真实模型适配验收

### Config 检查（不暴露 key）

```bash
# 查看当前 provider 配置
curl -s http://localhost:8005/api/llm/config | python3 -m json.tool
```

预期结果：`api_key_configured` 反映是否配置了 API key，响应中不包含 `api_key` 字段。

### Real Provider 手动测试（需设置 .env）

```bash
# .env 中设置
# AI_PROVIDER=openai_compatible
# AI_BASE_URL=<your-api-endpoint>
# AI_API_KEY=<your-key>
# AI_MODEL=<model-name>

curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello"}' | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'model:',r['model'],'usage:',r['usage'],'finish_reason:',r['finish_reason'])
"
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [OpenAI-Compatible Provider](docs/openai-compatible-provider.md)

## V0.6.0 Agent Template Contract Acceptance V0.6.0 智能体模板合同验收

### API 验证

```bash
# 列出模板
curl -s http://localhost:8005/api/agent-templates | python3 -m json.tool

# 查询单个模板
curl -s http://localhost:8005/api/agent-templates/generic_agent | python3 -c "
import json,sys;t=json.load(sys.stdin)
print('id:',t['id'],'provider:',t['provider'],'tools:',t['tools'])
"

# 不存在的模板返回 404
curl -s -o /dev/null -w '%{http_code}' http://localhost:8005/api/agent-templates/unknown
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Agent Template Contract](docs/agent-template-contract.md)

## V0.6.1 Agent YAML Config Loader Acceptance V0.6.1 配置加载验收

### Config / Validate API

```bash
# 完整配置（嵌套 provider/tools/rag/workflow/eval）
curl -s http://localhost:8005/api/agent-templates/generic_agent/config | python3 -c "
import json,sys;c=json.load(sys.stdin)
print('provider:',c['provider'],'tools:',c['tools'],'rag:',c['rag']['enabled'])
"

# 校验
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate
# 预期: []
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Agent YAML Config](docs/agent-yaml-config.md)

## V0.6.2 Agent Template Registry API Acceptance V0.6.2 注册表 API 验收

### List / Validate

```bash
# 列表（含摘要字段）
curl -s http://localhost:8005/api/agent-templates | python3 -c "
import json,sys;ts=json.load(sys.stdin)
for t in ts: print(t['id'], t['provider_name'], 'tools:', t['tools_count'], 'rag:', t['rag_enabled'])
"

# 校验（结构化结果）
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:', r['valid'], 'errors:', len(r['errors']), 'warnings:', len(r['warnings']))
"
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Agent Template Registry API](docs/agent-template-registry-api.md)

## V0.6.3 Example Agent Template Acceptance V0.6.3 示例模板验收

### API 验证

```bash
# 查看 generic_agent 详情
curl -s http://localhost:8005/api/agent-templates/generic_agent | python3 -c "
import json,sys;t=json.load(sys.stdin)
print('id:',t['id'],'provider:',t['provider'],'tools:',len(t['tools']))
"

# 校验
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:',r['valid'])
"

# 查看模板目录 README
cat templates/agent-template/README.md
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Example Agent Template](docs/example-agent-template.md)

## V0.7.0 Workflow Contract Acceptance V0.7.0 工作流合同验收

### Validate 校验规则

`GET /api/agent-templates/generic_agent/validate` 返回 workflow 校验结果。
目前 `valid=true` 说明 workflow 结构正确。

```bash
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:', r['valid'], 'errors:', len(r['errors']))
"
```

### Workflow 校验规则

- entrypoint 必须引用已有 node id
- node id 不能重复
- edge from/to 必须引用已有 node id
- 不允许自环
- terminal_nodes 必须引用已有 node id
- node type 必须在允许列表中

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Workflow Contract](docs/workflow-contract.md)

## V0.7.1 Node / Edge / Condition Schema Enhancement V0.7.1 Node/Edge/Condition Schema 增强

本节覆盖 WorkflowNode / WorkflowEdge / WorkflowCondition 的增强校验。

### Validate

```bash
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:', r['valid'], 'errors:', len(r['errors']), 'warnings:', len(r['warnings']))
"
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

## V0.7.2 Built-in Workflow Nodes Acceptance V0.7.2 内置工作流节点验收

### Contract 校验

`generic_agent` 的 workflow 节点已更新为 dict 格式，展示完整 contract 用法。

```bash
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:', r['valid'], 'errors:', len(r['errors']), 'warnings:', len(r['warnings']))
"
```

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Built-in Workflow Nodes](docs/workflow-built-in-nodes.md)

## V0.7.3 Workflow Validation / Eval Acceptance V0.7.3 校验与评估验收

### Workflow Eval

```bash
python3 scripts/run_workflow_evals.py
```

预期结果：

```
PASS valid_workflow
Summary: 1 passed, 0 failed, 1 total
```

### Error Codes

Workflow 校验错误现在包含结构化 error_items：

| Code | Severity |
|---|---|
| WORKFLOW_ENTRYPOINT_MISSING | error |
| WORKFLOW_NODE_DUPLICATE | error |
| WORKFLOW_EDGE_TARGET_NOT_FOUND | error |
| WORKFLOW_NODE_TYPE_UNSUPPORTED | error |
| WORKFLOW_SELF_LOOP | error |
| WORKFLOW_TERMINAL_NODE_NOT_FOUND | error |
| WORKFLOW_RAG_RETRIEVAL_MODE_INVALID | warning |
| WORKFLOW_CONDITION_TYPE_UNSUPPORTED | warning |
| WORKFLOW_CONFIG_KEY_UNKNOWN | warning |
| WORKFLOW_EXPECTED_OUTPUT_MISSING | warning |
| WORKFLOW_DECISION_ROUTE_NOT_FOUND | warning |

### Full Regression 完整回归

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
npm run build --prefix apps/web
python3 scripts/check_business_terms.py
```

### 文档参考

- [Workflow Validation](docs/workflow-validation.md)

## V0.7.x Workflow Contract Summary V0.7.x Workflow 验收总结

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试
make test-api

# Agent trajectory eval
python3 scripts/run_evals.py

# RAG retrieval eval
python3 scripts/run_rag_evals.py

# Workflow validation eval
python3 scripts/run_workflow_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web
```

### Validate API

```bash
# 验证 generic_agent workflow 结构
curl -s http://localhost:8005/api/agent-templates/generic_agent/validate | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('valid:', r['valid'], 'errors:', len(r['errors']), 'warnings:', len(r['warnings']))
"
```

### Eval Runner

```bash
python3 scripts/run_workflow_evals.py
```

预期输出：

```
PASS valid_workflow
Summary: 1 passed, 0 failed, 1 total
```

### 文档参考

- [Workflow Contract](docs/workflow-contract.md)
- [Built-in Workflow Nodes](docs/workflow-built-in-nodes.md)
- [Workflow Validation](docs/workflow-validation.md)
