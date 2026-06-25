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
