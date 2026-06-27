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

## V0.8.1 Policy Validation Evals Acceptance V0.8.1 Policy Eval 验收

V0.8.1 新增独立 policy validation eval runner，7 个 eval case 覆盖
valid / invalid 场景。只验证 contract 结构，不执行 policy。

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

# Policy validation eval（预期 7 passed）
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### Eval Cases

| Case | 预期 |
|---|---|
| `valid_policy` | valid=true |
| `valid_empty_policy_list` | valid=true |
| `invalid_scope` | valid=false, POLICY_SCOPE_INVALID |
| `invalid_action` | valid=false, POLICY_ACTION_INVALID |
| `invalid_condition_type` | valid=false, POLICY_CONDITION_TYPE_INVALID |
| `invalid_guardrail_type` | valid=false, GUARDRAIL_TYPE_INVALID |
| `invalid_guardrail_policy_ref` | valid=true (warning only), GUARDRAIL_POLICY_REF_NOT_FOUND |

### 行为不变性检查

- PolicyValidator 只做结构校验，不执行 condition
- 所有已有 tests / eval / API 不变
- 不改 runtime

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.2 Guardrail Decision Contract Acceptance V0.8.2 决策合同验收

V0.8.2 新增 GuardrailDecision / DecisionResult 合同，用于描述标准化决策结果。
只做 contract / schema / validator / docs / tests，不执行 policy。

### Contract 合同

| 模型 | 说明 |
|---|---|
| `GuardrailDecision` | 单条决策：decision_id / action / severity / reason / matched_rules |
| `DecisionResult` | 聚合结果：valid / final_action / decisions / errors / warnings |

action 枚举：`allow`, `block`, `warn`, `require_review`
severity 枚举：`low`, `medium`, `high`, `critical`

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 296 passed）
make test-api

# Agent trajectory eval（预期 8 passed）
python3 scripts/run_evals.py

# RAG eval（预期 2 passed）
python3 scripts/run_rag_evals.py

# Workflow eval（预期 1 passed）
python3 scripts/run_workflow_evals.py

# Policy validation eval（预期 11 passed）
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### 行为不变性检查

- PolicyValidator.validate_decision_contract / validate_decision_result **只做结构校验**
- 不生成决策、不执行 policy、不调用外部系统
- 所有已有 API / tests / eval 不变

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.3 Guardrail Evaluation Context Contract Acceptance V0.8.3 评估上下文合同验收

V0.8.3 新增 EvaluationContext / EvaluationSubject 合同，用于描述 policy /
guardrail 评估上下文结构。只做 contract / schema / validator / docs / tests，
不执行 policy。

### Contract 合同

| 模型 | 说明 |
|---|---|
| `EvaluationContext` | 评估上下文：context_id / scope / subject / attributes / metadata |
| `EvaluationSubject` | 评估主体：type / id / content / payload / metadata |

scope 枚举：`input`, `output`, `tool`, `rag`, `provider`, `workflow`

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 309 passed）
make test-api

# Agent trajectory eval（预期 8 passed）
python3 scripts/run_evals.py

# RAG eval（预期 2 passed）
python3 scripts/run_rag_evals.py

# Workflow eval（预期 1 passed）
python3 scripts/run_workflow_evals.py

# Policy validation eval（预期 16 passed）
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### 行为不变性检查

- PolicyValidator.validate_evaluation_context **只做结构校验**
- 不根据 context 执行 policy、不生成决策、不调用外部系统
- 所有已有 API / tests / eval 不变

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.4 Policy Dry-Run Evaluator Acceptance V0.8.4 策略 Dry-Run 评估器验收

V0.8.4 新增业务无关的 PolicyDryRunEvaluator，根据 Policy / Guardrail /
EvaluationContext 生成 DecisionResult。支持 always / match / route condition，
expression 安全拒绝。**不接 runtime，不拦截请求**。

### 已实现能力

- ✅ always condition → 按 rule action 生成 decision
- ✅ match condition → field + equals/contains/exists 结构匹配
- ✅ route condition → route_key 存在性匹配
- ✅ expression condition → 安全拒绝（require_review + unsupported_expression）
- ✅ final_action 按优先级合并：block > require_review > warn > allow
- ✅ guardrail policy_ref 解析
- ✅ guardrail scope 过滤

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 309 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查和前端构建
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### Eval Cases

6 个 dry_run eval case（共 22 个 policy eval case）：

| Case | 预期 final_action |
|---|---|
| dry_run_allow_always | allow |
| dry_run_warn_match | warn |
| dry_run_block_match | block |
| dry_run_require_review_route | require_review |
| dry_run_unsupported_expression | require_review |
| dry_run_guardrail_policy_ref_missing | require_review |

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.5 Guardrail Runtime Integration Plan Acceptance V0.8.5 运行时集成计划验收

V0.8.5 只产出集成计划文档，**不修改任何代码**。

### 文档产出

- `docs/guardrail-runtime-integration-plan.md`：完整的 runtime 集成设计，包括
  execution mode、7 个接入点设计、DecisionResult handling、dry-run/enforcement 边界、
  未来版本路线

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 301 passed，纯文档阶段）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py

# 前端构建
npm run build --prefix apps/web

# Git diff whitespace 检查
git diff --check
```

### 验收确认项

- ✅ 不修改任何 runtime 模块
- ✅ 不新增 API endpoint
- ✅ 不实现 enforcement
- ✅ 不接真实请求链路
- ✅ 不创建业务 Agent
- ✅ 所有现有测试不变
- ✅ 所有现有 eval 不变

## V0.8.6 Input Guardrail Dry-Run Hook Acceptance V0.8.6 输入护栏 Dry-Run Hook 验收

V0.8.6 新增 `run_input_guardrail()` dry-run hook，在 RunStore._create_run
中构造 input-scope EvaluationContext，调用 PolicyDryRunEvaluator，
记录 `guardrail.dry_run.completed` event。纯 dry-run，不拦截请求，
不改变 API response 主结构。

### 已实现能力

- ✅ `dry_run_hooks.py` — `run_input_guardrail()` helper
- ✅ RunStore._create_run 接入点（run.started 后、execute_module 前）
- ✅ EvaluationContext: scope=input, subject.type=run_input
- ✅ 没有 policies/guardrails 时 no-op，不记录事件
- ✅ 异常安全——hook 不抛出，不影响 run 创建
- ✅ final_action=block 时仍继续执行 run

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 314 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查和前端构建
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.7 Tool Guardrail Dry-Run Hook Acceptance V0.8.7 工具护栏 Dry-Run Hook 验收

V0.8.7 复用已有 `run_tool_guardrail()` 接入 ToolExecutionPipeline。
构造 tool-scope EvaluationContext，调用 PolicyDryRunEvaluator，
记录 `guardrail.dry_run.completed` event。纯 dry-run，不阻止 tool 执行。

### 已实现能力

- ✅ `run_tool_guardrail()` 接入 ToolExecutionPipeline._execute_tool
- ✅ EvaluationContext: scope=tool, subject.type=tool_call
- ✅ 没有 policies/guardrails 时 no-op，不影响现有 tool tests
- ✅ 异常安全——hook 不抛出，不影响 tool 执行
- ✅ final_action=block 时仍继续执行 tool
- ✅ ToolCall / tool result / timeout / retry / permission / sandbox 行为完全不变

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 318 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查和前端构建
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.8 Provider / RAG Guardrail Dry-Run Helpers Acceptance V0.8.8 Provider / RAG 护栏 Helper 验收

V0.8.8 复用已有 `run_provider_guardrail()` / `run_rag_guardrail()` helper
（均在 `dry_run_hooks.py` 中），新增 6 条测试。当前不做 runtime wiring——
provider_runtime / rag runtime 没有 run_id / trace_id / event_repository 上下文。
纯 helper，不接入运行链路。

### 已实现能力

- ✅ `run_provider_guardrail()` — 构造 provider-scope EvaluationContext，返回 DecisionResult dict
- ✅ `run_rag_guardrail()` — 构造 rag-scope EvaluationContext，返回 DecisionResult dict
- ✅ 没有 policies/guardrails 时返回 `{"_noop": True}`
- ✅ final_action=block 时只返回 DecisionResult，不阻断

### 为什么不接入 runtime

| Runtime | Has event_repository? | Has run_id? | 当前方式 |
|---|---|---|---|
| RunStore (input hook) | ✅ Yes | ✅ Yes | 记录 event（V0.8.6） |
| ToolExecutionPipeline (tool hook) | ✅ Yes | ✅ Yes | 记录 event（V0.8.7） |
| provider_runtime/router.py | ❌ No | ❌ No | helper → 返回 dict |
| harness/rag/store.py | ❌ No | ❌ No | helper → 返回 dict |

未来 runtime 调用链携带 run context 时再接入 event recording。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 324 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查和前端构建
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)

## V0.8.9 Docs Consolidation Acceptance V0.8.9 文档收口验收

V0.8.9 只做文档收口，不修改任何代码，不改测试，不改 runtime。

### V0.8 Supported / Not Supported

当前支持：
- Policy / Guardrail / Rule / Condition 合同及 JSON Schema
- PolicyValidator 结构校验及 22 个 eval case
- GuardrailDecision / DecisionResult / EvaluationContext 合同
- PolicyDryRunEvaluator（always / match / route / expression 安全拒绝）
- Input guardrail dry-run hook（接入 RunStore）
- Tool guardrail dry-run hook（接入 ToolExecutionPipeline）
- Provider / RAG guardrail dry-run helpers（helper-level）

当前不支持：
- Enforcement — 不拦截请求
- Blocking — block 仅作为 decision 记录
- Human review routing
- Modifying output
- Changing run status / tool / provider / RAG results

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 324 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查和前端构建
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Policy Guardrail Contract](docs/policy-guardrail-contract.md)
- [Guardrail Runtime Integration Plan](docs/guardrail-runtime-integration-plan.md)

## V0.9.0 CLI / Scaffold Contract Acceptance V0.9.0 CLI 脚手架合同验收

V0.9.0 是纯文档阶段——新增 `docs/cli-scaffold-contract.md`，设计 CLI / Scaffold
方案。**不实现 CLI 代码，不修改运行时模块。**

### 文档产出

- `docs/cli-scaffold-contract.md`：覆盖命令设计（3 级）、scaffold 生成物范围、
  命名规则、dry-run/preview/overwrite 模式、安全规则、V0.9 路线图

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 324 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)

## V0.9.1 Scaffold Module Script Acceptance V0.9.1 Module 脚手架验收

V0.9.1 新增 `scripts/scaffold_module.py`，支持 argparse 参数：
`--name`、`--dry-run`、`--preview`、`--force`。

### CLI 参数

| 参数 | 说明 |
|---|---|
| `--name NAME, -n NAME` | Module name in snake_case（必填） |
| `--dry-run` | 打印将创建的文件，不写入 |
| `--preview` | `--dry-run` 的别名 |
| `--force` | 覆盖已存在的目标目录 |

### 命名校验

- snake_case: `^[a-z][a-z0-9_]*$`
- 长度 ≤ 64
- 拒绝 path traversal（`..`、`/`、`\`）
- 拒绝 sensitive name（`.env`、`secret`、`key` 等）
- 拒绝 business term（`ecommerce`、`order`、`refund` 等）
- 拒绝以 `.` 开头

### 生成文件

`modules/<name>/` 下生成 7 个文件：
module.yaml、agent.yaml、README.md、services/<name>_service.py、prompts/system.md、skills/.gitkeep、evals/.gitkeep

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 346 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)
- [scripts/scaffold_module.py](scripts/scaffold_module.py)

## V0.9.2 Scaffold Agent Template Acceptance V0.9.2 Agent 模板脚手架验收

V0.9.2 新增 `scripts/scaffold_agent.py`，从 `templates/agent-template/agent.json`
读取源模板，生成业务无关的 agent 骨架。

### CLI 参数

| 参数 | 说明 |
|---|---|
| `--name NAME, -n NAME` | Agent name in snake_case（必填） |
| `--dry-run` | 打印将创建的文件，不写入 |
| `--preview` | `--dry-run` 的别名 |
| `--force` | 覆盖已存在的目标目录 |

### 生成文件

`templates/<name>/` 下生成 2 个文件：
- `agent.json` — 符合 AgentConfig contract，可被 AgentTemplateRegistry 识别
- `README.md` — 使用说明

### 源模板复用

`scripts/scaffold_agent.py` 读取 `templates/agent-template/agent.json`，
只替换 id / name / description / metadata，保持现有 contract 一致。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 370 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)
- [scripts/scaffold_agent.py](scripts/scaffold_agent.py)

## V0.9.3 Scaffold Eval Cases Acceptance V0.9.3 Eval Case 脚手架验收

V0.9.3 新增 `scripts/scaffold_eval.py`，生成 `evals/cases/<name>.json`。
字段精确匹配 `run_evals.py` 的 13 个 REQUIRED_FIELDS 和
`schemas/eval-case.schema.json`。使用 `demo_agent` 作为中性 module_id。

### CLI 参数

| 参数 | 说明 |
|---|---|
| `--name NAME, -n NAME` | Eval case name in snake_case（必填） |
| `--dry-run` | 打印将创建的文件，不写入 |
| `--preview` | `--dry-run` 的别名 |
| `--force` | 覆盖已存在的目标文件 |

### 生成文件

`evals/cases/<name>.json` — 包含 13 个字段，可被 `run_evals.py` 加载执行。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 395 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)
- [scripts/scaffold_eval.py](scripts/scaffold_eval.py)

## V0.9.4 Scaffold Docs Generator Acceptance V0.9.4 文档脚手架验收

V0.9.4 新增 `scripts/scaffold_docs.py`，生成 `docs/scaffolds/<kind>-<name>.md`。

### CLI 参数

| 参数 | 说明 |
|---|---|
| `--name NAME, -n NAME` | Name in snake_case（必填） |
| `--kind {module,agent,eval,generic}` | Scaffold kind（默认 generic） |
| `--dry-run` | 打印将创建的文件，不写入 |
| `--preview` | `--dry-run` 的别名 |
| `--force` | 覆盖已存在的目标文件 |

### 生成文件

`docs/scaffolds/<kind>-<name>.md` — 中性文档骨架，包含 Purpose /
Generated Files / How to Validate / How to Run Tests / Next Steps / Safety Notes。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 422 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)
- [scripts/scaffold_docs.py](scripts/scaffold_docs.py)

## V0.9.5 CLI Validation and Hygiene Acceptance V0.9.5 CLI 校验与工程卫生验收

V0.9.5 抽取 scaffold 系列脚本中重复的 validation 逻辑到共享模块
`scripts/scaffold_validation.py`。4 个 scaffold 脚本统一引用。

### 共享 API

| 函数 | 用途 |
|---|---|
| `validate_scaffold_name(name, kind="scaffold") -> list[str]` | 统一命名校验 |
| `resolve_safe_target(base_dir, target_name) -> Path` | 安全路径解析 |
| `format_errors(errors) -> str` | 错误格式化 |

### 抽取的重复逻辑

| 组件 | 之前 | 之后 |
|---|---|---|
| BUSINESS_TERMS | 4 份副本 | 1 份 |
| SENSITIVE_NAMES | 4 份副本 | 1 份 |
| NAME_PATTERN | 4 份副本 | 1 份 |
| validate_name() | 4 个独立实现 | 1 个统一实现 |
| resolve_target_path() | 4 个独立实现 | 1 个统一实现 |

### 行为不变性确认

- ✅ CLI 参数不变
- ✅ exit code 不变（0/1/2）
- ✅ 成功/失败语义不变
- ✅ 输出格式兼容
- ✅ 所有 481 已有测试通过

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 481 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)

## V0.9.6 CLI Docs Consolidation Acceptance V0.9.6 CLI 文档收口验收

V0.9.6 是纯文档阶段，不修改任何代码，不改 scaffold 脚本，不改测试。

### 新增文档

- `docs/cli-scaffold-guide.md`：4 个命令的 dry-run / normal / force 使用示例和验收方式
- `docs/cli-scaffold-troubleshooting.md`：7 种常见错误及修复方法

### V0.9 已实现能力总结

| 命令 | 脚本 | 生成目标 |
|---|---|---|
| Scaffold Module | `scripts/scaffold_module.py` | `modules/<name>/` |
| Scaffold Agent | `scripts/scaffold_agent.py` | `templates/<name>/` |
| Scaffold Eval | `scripts/scaffold_eval.py` | `evals/cases/<name>.json` |
| Scaffold Docs | `scripts/scaffold_docs.py` | `docs/scaffolds/<kind>-<name>.md` |
| Validation | `scripts/scaffold_validation.py` | 共享校验逻辑 |

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 业务词污染检查
python3 scripts/check_business_terms.py
npm run build --prefix apps/web
git diff --check
```

### CLI Dry-Run 验收

```bash
# 预览四个 scaffold 命令的输出（不写文件）
python3 scripts/scaffold_module.py --name sample_module --dry-run
python3 scripts/scaffold_agent.py --name sample_agent --dry-run
python3 scripts/scaffold_eval.py --name sample_eval --dry-run
python3 scripts/scaffold_docs.py --name sample_docs --kind generic --dry-run
```

### 文档参考

- [CLI Scaffold Contract](docs/cli-scaffold-contract.md)
- [CLI Scaffold Guide](docs/cli-scaffold-guide.md)
- [CLI Scaffold Troubleshooting](docs/cli-scaffold-troubleshooting.md)

## V1.0 Minimal Reusable Agent Harness Template Acceptance V1.0 模板验收

V1.0 重新定位项目为可复用 Agent Harness Template。新增快速启动、
模板使用指南、发布清单和健康检查脚本。**不修改 runtime。**

### 新增文件

| 文件 | 用途 |
|---|---|
| `QUICKSTART.md` | 10 分钟快速启动 |
| `TEMPLATE_USAGE.md` | fork/clone 分离指南 |
| `docs/template-release-checklist.md` | 发布清单 |
| `scripts/check_template_health.py` | 静态模板健康检查 |
| `apps/api/tests/test_template_health.py` | 6 条健康检查测试 |

### Template Health Checks

| 检查项 | 说明 |
|---|---|
| Key files | README, QUICKSTART, TEMPLATE_USAGE, Makefile, CLAUDE, AGENTS, docker-compose, check_business_terms |
| Scaffold scripts | 5 scaffold 脚本全部存在 |
| Template dirs | agent.json、module.yaml 存在 |
| .env git tracking | .env 不被 git 跟踪 |
| Business terms | 调用 check_business_terms.py 确认无污染 |

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py

# 前端构建
npm run build --prefix apps/web
git diff --check
```

### CLI Dry-Run 验收

```bash
python3 scripts/scaffold_module.py --name sample_module --dry-run
python3 scripts/scaffold_agent.py --name sample_agent --dry-run
python3 scripts/scaffold_eval.py --name sample_eval --dry-run
python3 scripts/scaffold_docs.py --name sample_docs --kind generic --dry-run
```

### 文档参考

- [Template Release Checklist](docs/template-release-checklist.md)
- [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)
- [QUICKSTART.md](QUICKSTART.md)

## V1.1 Multi-user Runtime Contract Acceptance V1.1 多用户运行时合同验收

V1.1 定义 UserContext / Conversation / Message / RunBinding 数据合同。
CreateRunRequest 新增可选 user context 字段。**不做 auth / RBAC / enforcement。**

### Contract Models

| Model | 必填字段 | 可选字段 |
|---|---|---|
| UserContext | user_id, tenant_id | roles |
| Conversation | conversation_id, tenant_id, user_id | agent_template_id, metadata |
| Message | message_id, conversation_id, tenant_id, user_id, role | content, request_id, idempotency_key, sequence_index |
| RunBinding | run_id, tenant_id, user_id | conversation_id, message_id |

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 507 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Multi-user Runtime Contract](docs/multi-user-runtime-contract.md)

## V1.2 Message / Conversation API Acceptance V1.2 消息与会话 API 验收

V1.2 实现 Conversation/Message CRUD API、conversation-triggered run、assistant message 回写。新增 DB 表自动创建。

### API Endpoints

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/conversations` | 创建 conversation |
| GET | `/api/conversations` | 列表（按 user_id / tenant_id） |
| GET | `/api/conversations/{id}` | 读取 conversation |
| POST | `/api/conversations/{id}/messages` | 添加消息（4 种角色） |
| GET | `/api/conversations/{id}/messages` | 消息列表（插入顺序） |
| POST | `/api/conversations/{id}/runs` | 创建 user message + run + assistant message |

### 新增 DB 表

| 表 | 字段 |
|---|---|
| `conversations` | id, user_id, tenant_id, agent_template_id, metadata, created_at, updated_at |
| `messages` | id, conversation_id(FK), tenant_id, user_id, role, content, run_id, metadata, created_at |

表通过 `Base.metadata.create_all` 自动创建，无迁移。

### Unified Acceptance Commands 统一验收命令

```bash
# 全量后端测试（当前预期 528 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Conversation Message API](docs/conversation-message-api.md)
- [Multi-user Runtime Contract](docs/multi-user-runtime-contract.md)

## V1.3 Tenant Isolation Acceptance V1.3 租户隔离验收

V1.3 为 Conversation/Message API 增加 tenant isolation。所有 conversation
操作必须携带 `tenant_id`。

### Tenant 规则

| 场景 | 状态码 |
|---|---|
| 缺少 `tenant_id` | 400 |
| `tenant_id` 不匹配 | 404 |
| `user_id` 不匹配（message/run） | 404 |
| `tenant_id` 匹配 + `user_id` 匹配 | 200/201 |

### Tenant Isolation 检查清单

| 检查项 | 结果 |
|---|---|
| GET conversations without tenant → 400 | ✅ |
| GET conversations with tenant → 200 | ✅ |
| GET conversations with tenant+user → 200 | ✅ |
| GET conversation without tenant → 400 | ✅ |
| GET conversation wrong tenant → 404 | ✅ |
| GET conversation own tenant → 200 | ✅ |
| GET messages without tenant → 400 | ✅ |
| GET messages wrong tenant → 404 | ✅ |
| GET messages own tenant → 200 | ✅ |
| POST message wrong tenant → 404 | ✅ |
| POST message wrong user → 404 | ✅ |
| POST conversation run wrong tenant → 404 | ✅ |
| POST conversation run wrong user → 404 | ✅ |
| Old POST /api/runs unchanged | ✅ |

### Unified Acceptance Commands

```bash
# 全量后端测试（当前预期 536 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Tenant Isolation](docs/tenant-isolation.md)

## V1.4 RAG Tenant Filter Acceptance V1.4 RAG 租户过滤验收

V1.4 为 RAG ingestion/retrieval 增加可选 tenant_id 过滤。

### 新增功能

- Ingestion（`POST /api/knowledge/documents`、`POST /api/knowledge/ingest`）接受可选 `tenant_id`
- Retrieval（`POST /api/knowledge/retrieve`）接受可选 `tenant_id`
- Tenant_id 存储在已有 metadata JSON 列（ChunkRecord.metadata_、DocumentRecord.metadata_）
- Keyword / Vector / Hybrid 三种检索模式都支持 tenant 过滤
- 向后兼容旧无 tenant 文档

### Unified Acceptance Commands

```bash
# 全量后端测试（当前预期 546 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [RAG Tenant Filter](docs/rag-tenant-filter.md)

## V1.5 Document Cleaning Pipeline Acceptance V1.5 文档清洗流水线验收

V1.5 离线文档清洗和入库流水线。支持 6 种文件类型，Plan A 文档级入库。

### 新增组件

| 组件 | 路径 | 说明 |
|---|---|---|
| 解析器 | `harness/ingestion/parsers/` | 6 个 parser（txt/md/pdf/docx/csv/xlsx） |
| 清洗器 | `harness/ingestion/cleaner.py` | 类型感知文本去噪音 |
| 预览 chunker | `harness/ingestion/chunker.py` | 预览 chunks（最终 chunking 由 RAG 负责） |
| 流水线 | `harness/ingestion/pipeline.py` | 扫描 → 解析 → 清洗 → chunk → manifest |
| CLI | `scripts/clean_documents.py` | 清洗命令 |
| CLI | `scripts/ingest_cleaned_docs.py` | 入库命令 |

### Metadata 流入路径

```
ingest_text(metadata={source_hash, document_key, ...})
  → Document.metadata (包含 tenant_id + metadata)
  → Chunk.chunk_metadata (包含 tenant_id + metadata)
  → V1.4 tenant filter 自动生效
```

### Unified Acceptance Commands

```bash
# 全量后端测试（当前预期 563 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Ingestion Pipeline](docs/ingestion-pipeline.md)

## V1.6 Tool Permission / Ownership Guard Acceptance V1.6 工具权限 / 所有权守卫验收

V1.6 为工具执行增加 ownership guard。已实现但文档待补充——详见 [Tool Permission Guard](docs/tool-permission-guard.md)。

## V1.7 Concurrency / Idempotency Contract Acceptance V1.7 并发 / 幂等合同验收

V1.7 增加 scoped idempotency_key 和 sequence_index 校验。

### IdempotencyGuard 设计

| 概念 | 说明 |
|---|---|
| Scoped key | `tenant_id\|user_id\|conversation_id\|action\|idempotency_key` |
| Sequence scope | `tenant_id\|conversation_id` |
| Storage | In-memory（单进程 MVP，进程重启丢失） |
| Singelen | `idempotency_guard` 模块级单例 |
| Reset | `guard.reset()` 用于测试隔离 |

### 幂等规则

| Code | 说明 |
|---|---|
| `LEGACY_SKIP` | 不传 key/seq 时跳过，兼容旧请求 |
| `ALLOWED` | 可以继续执行 |
| `DUPLICATE_IDEMPOTENCY_KEY` | 重复 key，返回已有 resource |
| `STALE_SEQUENCE` | sequence ≤ 已有最大值 |
| `SEQUENCE_GAP` | sequence > 最大值+1 |

### Unified Acceptance Commands

```bash
# 全量后端测试（当前预期 577 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Concurrency Idempotency Contract](docs/concurrency-idempotency-contract.md)

## V1.8 Async Job Queue / Worker Runtime Acceptance V1.8 异步任务队列验收

V1.8 新增 DB 后台异步任务队列和 Worker Runtime。

### Job 状态机

```
queued → running → succeeded
queued → running → failed
running → queued (retry, attempts < max_attempts)
queued → canceled (only queued)
```

### API Endpoints

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/jobs` | 创建 job（幂等入队） |
| GET | `/api/jobs` | 列表（可 tenant/status 过滤） |
| GET | `/api/jobs/{id}` | 详情 |
| POST | `/api/jobs/{id}/cancel` | 取消（仅 queued） |

### Idempotent Enqueue

Scoped key: `tenant_id | user_id | job_type | idempotency_key`

已有 job（任何状态）重复 key → 返回已有 job。

### CLI Worker

```bash
python3 scripts/run_worker_once.py
```

### Unified Acceptance Commands

```bash
# 全量后端测试（当前预期 599 passed）
make test-api

# 所有 eval runner
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# 模板健康检查
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
npm run build --prefix apps/web
git diff --check
```

### 文档参考

- [Async Job Worker Runtime](docs/async-job-worker-runtime.md)

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
