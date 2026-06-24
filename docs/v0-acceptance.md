# V0 Acceptance V0 总体验收

本文档用于验收 Agent Harness Template V0。V0 是业务无关的通用 Agent 应用底座，默认示例只用于验证框架链路，不绑定具体行业。

## V0 已完成能力清单

- Stage 1：基础项目骨架，包括 Next.js 前端首页、FastAPI `/health`、PostgreSQL、Redis、`.env.example`、Makefile 和基础测试。
- Stage 2：Agent Run 主链路，包括 Task / Run / Step 最小模型、`demo_agent` mock response、Run 查询和 Event 查询。
- Stage 3：AI Runtime + Registry，包括 Mock LLM、OpenAI-compatible provider 基础结构、structured output 最小解析、module / skill / tool registry。
- Stage 4：Artifact + 文件上传，包括 `.txt` / `.md` 上传、File 查询、Run Artifact 创建与查询、本地文件存储和最小文本提取。
- Stage 5A：LangGraph 最小状态机，包括 `input_node`、`skill_node`、`tool_node`、`final_node`，并记录 Step / Event。
- Stage 5B：RAG 最小版，包括文档 ingest、简单 chunking、关键词检索、citation 返回和 knowledge API。
- Stage 5C：Module Scaffold 脚手架，包括通用 module template 和 `cli/scaffold_module.py`。

## 访问地址

- 前端：`http://localhost:3005`
- 后端：`http://localhost:8005`
- 后端健康检查：`http://localhost:8005/health`
- PostgreSQL：`localhost:15432`
- Redis：`localhost:16379`

## 通用启动命令

安装依赖：

```bash
make install
```

启动 PostgreSQL 和 Redis：

```bash
make up
```

启动后端：

```bash
make dev-api
```

启动前端：

```bash
make dev-web
```

运行后端测试：

```bash
make test-api
```

构建前端：

```bash
cd apps/web && npm run build
```

停止基础设施：

```bash
make down
```

## Stage 1 验收命令

```bash
curl http://localhost:8005/health
```

预期结果：

```json
{
  "status": "ok",
  "service": "agent-harness-api"
}
```

前端验收：

```text
http://localhost:3005
```

## Stage 2 验收命令

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID
curl http://localhost:8005/api/runs/$RUN_ID/events
```

预期结果：

- Run 可以创建并完成。
- Run 详情包含 Step。
- Event 列表包含 Run 和 Step 的最小日志。

## Stage 3 验收命令

```bash
curl http://localhost:8005/api/modules
curl http://localhost:8005/api/skills
curl http://localhost:8005/api/tools

curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}'

curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock","structured":true}'
```

预期结果：

- registry API 返回本地静态注册信息。
- mock LLM smoke 可以返回结果。
- structured output 最小解析返回成功状态。

## Stage 4 验收命令

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

预期结果：

- 只接受 `.txt` 和 `.md` 文件。
- 上传文件使用内部 ID 文件名保存。
- Artifact 可以关联到 Run 并查询。

## Stage 5A 验收命令

```bash
RUN_ID=$(curl -s -X POST http://localhost:8005/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"hello"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl http://localhost:8005/api/runs/$RUN_ID
curl http://localhost:8005/api/runs/$RUN_ID/events
```

预期 Step / Event 包含这些节点：

- `input_node`
- `skill_node`
- `tool_node`
- `final_node`

## Stage 5B 验收命令

```bash
FILE_ID=$(curl -s -X POST http://localhost:8005/api/files/upload \
  -F "file=@README.md" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")

curl -X POST http://localhost:8005/api/knowledge/ingest \
  -H 'Content-Type: application/json' \
  -d "{\"file_id\":\"$FILE_ID\"}"

curl http://localhost:8005/api/knowledge/documents

curl -X POST http://localhost:8005/api/knowledge/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"Agent Harness","limit":3}'
```

预期结果：

- ingest 返回 Document 和 Chunk。
- documents 返回已 ingest 文档。
- retrieve 返回结果和 citation。

## Stage 5C 验收命令

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

重复执行：

```bash
python3 cli/scaffold_module.py sample_agent
```

预期结果：

- 命令失败。
- 不覆盖已有 `modules/sample_agent`。

## 常见错误排查

### `python: command not found`

使用 `python3`，或通过 Makefile 变量指定 Python：

```bash
make install-api PYTHON=/path/to/python
```

### `pytest: command not found`

后端依赖可能尚未安装：

```bash
make install-api
make test-api
```

### 前端显示 API `unavailable`

通常表示后端未启动。先运行：

```bash
make dev-api
```

然后刷新：

```text
http://localhost:3005
```

### 端口被占用

默认端口：

- 前端：`3005`
- 后端：`8005`
- PostgreSQL：`15432`
- Redis：`16379`

如 PostgreSQL 或 Redis 端口冲突，可在 `.env` 中调整 `POSTGRES_PORT` 或 `REDIS_PORT`。

### Docker credential helper error

项目使用本地 Docker config：

```text
.docker
```

请通过 Makefile 启动：

```bash
make up
```

### 文件上传失败

V0 只支持 `.txt` 和 `.md`。请确认上传文件类型符合限制，并确认后端进程对 `apps/api/data/uploads` 有写入权限。

### scaffold 提示 module 已存在

脚手架会阻止覆盖已有模块。请更换模块名，或手动确认旧模块不再需要后再处理。

## 当前限制

- V0 默认使用 Mock LLM，主链路不依赖真实外部模型。
- RAG V0 只做简单全文检索或关键词匹配，不包含 embedding、向量数据库或 rerank。
- 文件上传只支持 `.txt` 和 `.md`。
- Artifact 只做最小关联和查看，不包含复杂预览。
- LangGraph 仅用于最小可观察状态机，不包含复杂 workflow planner 或生产级 checkpoint。
- Scaffold 只生成通用模块骨架，不包含 Eval Runner 或复杂模板引擎。
- V0 不包含 Human Review、多模态、生产级权限系统、远程 skill 或插件市场。
