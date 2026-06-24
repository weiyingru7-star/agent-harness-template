# Schema Contracts 核心契约

V0.1.3 为 Agent Harness Template 的核心对象补齐最小 JSON Schema 草案。它们用于统一后续模块、工具、技能、workflow 和 eval 的开发语言。

这些 schema 是通用契约草案，不会改变现有 API 行为，也不会自动接入运行时代码。

## 统一规范

- 使用 JSON Schema draft 2020-12。
- 字段命名使用 `snake_case`。
- 核心标识字段统一为 `id`。
- 外键引用字段使用 `xxx_id`，例如 `run_id`、`task_id`、`module_id`、`file_id`。
- 时间字段使用 `created_at`、`updated_at`。
- 状态字段使用 `status`。
- 只定义通用最小字段。
- 不包含具体行业字段。

## Schema 清单

- `schemas/task.schema.json`：用户提交任务的最小契约。
- `schemas/run.schema.json`：Agent 执行 run 的最小契约。
- `schemas/step.schema.json`：Run 内部 step 的最小契约。
- `schemas/artifact.schema.json`：Run 关联产物的最小契约。
- `schemas/file.schema.json`：上传文件资源的最小契约。
- `schemas/document.schema.json`：已 ingest 文档的最小契约。
- `schemas/chunk.schema.json`：文档切分片段的最小契约。
- `schemas/module.schema.json`：模块定义的最小契约。
- `schemas/agent.schema.json`：Agent 定义的最小契约。
- `schemas/skill.schema.json`：Skill 定义的最小契约。
- `schemas/tool.schema.json`：Tool 定义的最小契约。
- `schemas/workflow.schema.json`：Workflow 定义的最小契约。
- `schemas/event.schema.json`：Run 或 Step 事件的最小契约。
- `schemas/provider.schema.json`：AI Runtime provider 的最小契约。
- `schemas/policy.schema.json`：通用策略定义的最小契约。
- `schemas/eval-case.schema.json`：单条 eval case 的最小契约。

## 对象关系

- Task 可以产生一个或多个 Run，Run 可通过 `task_id` 关联 Task。
- Run 可通过 `module_id` 和 `agent_id` 标记使用的模块和 Agent。
- Step 通过 `run_id` 归属于 Run。
- Event 通过 `run_id` 归属于 Run，也可以通过 `step_id` 关联 Step。
- Artifact 通过 `run_id` 归属于 Run，也可以通过 `file_id` 关联 File。
- Agent 通过 `module_id` 归属于 Module。

## 使用方式

- 新模块的 `module.yaml` 应参考 `schemas/module.schema.json`。
- 新模块的 `agent.yaml` 应参考 `schemas/agent.schema.json`。
- 新 skill 和 tool 的配置应参考对应 schema。
- workflow 草案应参考 `schemas/workflow.schema.json`。
- eval case 草案应参考 `schemas/eval-case.schema.json`。

## 当前限制

- 这些 schema 不做运行时强制校验。
- 这些 schema 不代表新增 API。
- 这些 schema 不实现真实外部模型、embedding、向量数据库、多模态、人审、权限或 Eval Runner。
- 后续如果 schema 需要成为运行时校验的一部分，应先提交底座变更申请。
