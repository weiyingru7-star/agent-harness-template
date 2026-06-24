# Project Boundaries 项目边界

本文档定义 Stage 1 期间哪些内容可以改，哪些内容不能改。

## Stage 1 Allowed Scope Stage 1 允许范围

Stage 1 只允许修改最小项目骨架：

- 根目录配置文件和文档
- `apps/web` 前端基础骨架
- `apps/api` 后端基础骨架
- PostgreSQL 和 Redis 的 Docker Compose 配置
- 后端基础健康检查测试

## Stage 1 Allowed Directories And Files Stage 1 允许修改的目录和文件

允许修改的根目录文件：

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_BOUNDARIES.md`
- `TASK_SPEC.md`
- `TESTING.md`
- `CHANGELOG.md`
- `README.md`
- `.env.example`
- `.gitignore`
- `Makefile`
- `docker-compose.yml`

允许修改的前端目录：

- `apps/web`

允许修改的后端目录：

- `apps/api`

## Stage 1 Forbidden Directories Stage 1 禁止目录

除非用户明确切换阶段，否则 Stage 1 不允许创建或修改以下目录：

- `core`
- `ai_runtime`
- `harness`
- `skills`
- `tools`
- `modules`
- `templates`
- `cli`
- `schemas`
- `evals`

这些目录保留给后续阶段使用。

## Stage 2-5 Boundary Stage 2-5 边界

Stage 1 期间禁止提前创建、脚手架化或部分实现以下能力：

- Stage 2：Agent Run 主链路、Task、Run、Step、Event、`demo_agent`
- Stage 3：AI Runtime、skill registry、tool registry、provider registry
- Stage 4：Artifact model、file upload、text extraction、artifact viewer
- Stage 5：RAG、LangGraph state machine、scaffold command、module template

## `apps/web` Boundary `apps/web` 修改边界

Stage 1 允许：

- 首页
- API 健康状态展示
- 基础 API helper
- 最小样式
- 前端包配置

Stage 1 禁止：

- Chat UI
- Run detail pages
- Agent forms
- File upload UI
- Artifact UI
- Module selection UI
- RAG UI

## `apps/api` Boundary `apps/api` 修改边界

Stage 1 允许：

- FastAPI app 启动
- `/health`
- 最小配置
- `/health` 基础测试

Stage 1 禁止：

- ORM setup
- Database models
- Redis client integration
- Agent routes
- Run routes
- File routes
- RAG routes
- LLM routes

## Documentation Boundary 文档边界

文档可以描述后续阶段规划，但不能暗示这些能力已经实现。

文档必须清楚区分：

- 当前 Stage 1 已有行为
- 未来计划能力
- 禁止提前实现的内容

## Root Configuration Boundary 根目录配置边界

根目录配置可以包含：

- Stage 1 的 Make 命令
- PostgreSQL 和 Redis 的 Docker Compose 配置
- 安全的环境变量示例
- 仓库开发规范文档

根目录配置不能包含：

- 生产部署逻辑
- CI/CD pipelines
- Agent runtime configuration
- 模型 provider 密钥
- 业务专用配置
