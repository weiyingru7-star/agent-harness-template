# Claude Code Development Rules Claude Code 开发规则

本仓库是一个**业务无关的通用 Agent Harness 模板**。Claude Code 必须尊重当前阶段边界，不能提前实现未来阶段功能。

## Project Goal 项目目标

创建一个可复用的 AI Agent 应用模板，用来支持未来各种 Agent 项目，而不是绑定某一个具体业务。

未来阶段可以加入 agent runtime、ai runtime、registries、memory、RAG、files、workflows、human review、observability 和 evals。但除非当前任务明确要求，否则这些能力都不能提前加入。

## Current Stage 当前阶段

当前阶段：Stage 1。

Stage 1 只允许包含：

- Next.js 前端首页
- FastAPI `/health`
- PostgreSQL 和 Redis 的 Docker Compose 配置
- `.env.example`
- Makefile
- README
- AI 开发约束文档
- `test_health.py`

## Do Not Implement Early 禁止提前实现

不要创建或实现：

- Agent logic
- Run / Step / Event / Task / Artifact models
- AI Runtime
- LLM providers
- Database ORM
- RAG
- File upload
- Skill registry
- Tool registry
- LangGraph state machine
- Human review
- Evals
- Business-specific modules
- Stage 2-5 directories

## File Modification Rules 文件修改规则

- 只修改当前任务点名或明确需要的文件。
- 不要编辑无关的前端、后端、基础设施或文档文件。
- 不要做大范围重构。
- 不要删除已有可用行为。
- 未经明确批准，不要重命名或移动文件。
- 不要为未来阶段偷偷添加隐藏抽象。

## Required Workflow 必须遵守的流程

修改文件前：

- 说明计划创建或修改哪些文件。
- 说明每个文件为什么属于当前任务范围。
- 如果任务边界不清楚，先问用户。

修改文件后：

- 列出每个被修改的文件。
- 总结具体改动。
- 给出验收命令。
- 说明是否运行了测试。

## Uncertainty Rule 不确定时的规则

不确定时先提问。不要推断未来需求，不要实现推测性的功能。

## Stage 1 Commands Stage 1 命令

- `make install-api`
- `make install-web`
- `make install`
- `make dev-api`
- `make dev-web`
- `make test-api`
- `make up`
- `make down`
