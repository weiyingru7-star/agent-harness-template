# Project Boundaries 项目边界

本文档定义 Agent Harness Template（当前 V0.3.0）的修改边界与硬约束。所有协作者（含 AI 协作者）在改动本仓库前必须先对照本文档。

## Business-Agnostic Principle 业务无关原则

`agent-harness-template` 是通用 Agent 底座，核心代码、核心文档、默认页面和示例模块不允许绑定任何具体行业。

禁止在模板核心中写死具体行业、业务场景或领域实体名称。具体行业只能出现在 `modules/{module_name}/` 业务模块中，且模块必须由使用者自行创建，模板不自带业务 Agent。

如需示例，只能使用中性表达，例如：文档助手、流程助手、分析助手、example agent。

## Current Directory Roles 各目录当前角色

V0.3.0 各顶层目录的角色与修改纪律：

- `apps/api/`：FastAPI 后端，承载 Run / Step / Event 主链路与全部 REST API。允许增量开发，但不得改现有 API 路径与响应契约。
- `apps/web/`：Next.js 前端，承载首页、run 表单、run 详情与 Timeline 视图。允许增量开发，不得删除已有页面。
- `core/`：跨模块共享基础（db / config / cache / security / observability / utils / storage）。修改需谨慎，不得破坏 `core/db` 的现有模型与初始化协议。
- `harness/`：蓝图目录，多数子目录仅含 README 占位，实际 runtime 逻辑在 `apps/api/app/services/`。不得在此目录凭空实现与 `apps/api` 重复的运行时。
- `ai_runtime/`：AI runtime 蓝图目录，实际 provider/router 在 `apps/api/app/ai_runtime/`。
- `modules/`：业务模块目录。模板只提供中性示例模块（`demo_agent`、`sample_agent`、`example_agent`）。不得在模板核心中预置任何具体行业模块。
- `schemas/`：JSON Schema 草案，按统一规范维护（见 `docs/schema-contracts.md`）。
- `evals/`：eval cases 与 eval runner 数据，配合 `scripts/run_evals.py`。
- `cli/`：`scaffold_module.py` 脚手架入口。
- `scripts/`：`check_business_terms.py`（业务词污染检查）、`run_evals.py`（eval runner）。
- `templates/`：`module-template/`，被 `cli/scaffold_module.py` 使用。
- `docs/`：项目文档，需与当前版本实况一致，不得保留过时的阶段声明。
- `infra/`：基础设施配置占位。

## Hard Constraints 硬约束

以下 API 路径是已发布契约，禁止修改路径、方法或响应结构：

- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/trace`
- `GET /api/runs/{run_id}/checkpoints`
- `GET /api/runs/{run_id}/timeline`
- `POST /api/runs/{run_id}/retry`
- `GET /api/runs/{run_id}/tool-calls`
- `GET /api/tool-calls/{tool_call_id}`

数据库表结构（`tasks`、`runs`、`steps`、`run_events`、`files`、`artifacts`、`documents`、`chunks`、`checkpoints`、`tool_calls`）不得擅自重命名或删除字段；新增字段需保持向后兼容。

## Modification Discipline 修改纪律

- 不要创建任何业务 Agent。
- 禁止在模板核心加入电商、客服、服装、CAD、订单、售后、自媒体、竞品、灯具、报价等业务逻辑。
- 不要大规模重构。
- 不要修改上文列出的现有 API 路径。
- 修改前先说明计划，不要直接写代码。
- 每次完成后必须给出：修改文件列表、改动理由、验收命令、是否破坏旧接口、commit message。

## Documentation Boundary 文档边界

文档必须与当前版本实况一致，清楚区分：

- 当前已实现的行为
- 未来计划能力
- 禁止提前实现的内容

过时的阶段声明（例如历史 Stage 1 范围）应及时清理，不得与新版本描述并存。

## Business Term Check 业务词污染检查

`scripts/check_business_terms.py` 用于扫描模板核心文件是否混入业务词。提交前应运行：

```bash
python3 scripts/check_business_terms.py
```

新增业务词需先在此脚本的黑名单中登记，并确认对应内容只出现在 `modules/` 内的业务模块中。
