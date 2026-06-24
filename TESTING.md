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
