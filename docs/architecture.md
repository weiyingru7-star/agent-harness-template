# Architecture 架构说明

Agent Harness Template 是业务无关的通用 Agent 应用底座。V0.1.1 的目标是让目录结构更接近完整蓝图，同时保持 V0.1.0 的可运行能力稳定。

## 当前已实现能力

- `apps/web/`：Next.js 前端，支持首页、任务提交和 Run 详情查看。
- `apps/api/`：FastAPI 后端，提供健康检查、Run、Registry、LLM smoke、File、Artifact、Knowledge API。
- `modules/demo_agent/`：通用 demo agent，使用 mock response 验证主链路。
- `core/storage/`：本地文件存储最小实现。
- `harness/state_machine/`：demo agent 的最小可观察状态机。
- `harness/rag/`：基于已上传 `.txt` / `.md` 文件的最小知识检索。
- `templates/module-template/`：新模块脚手架模板。
- `cli/scaffold_module.py`：创建新模块的最小脚手架命令。

## V0.1.1 蓝图目录

V0.1.1 新增的目录主要是边界说明和未来扩展位置，不代表功能已经实现。

- `core/config/`：共享配置边界。
- `core/db/`：数据库基础设施边界。
- `core/cache/`：缓存基础设施边界。
- `core/security/`：安全能力边界。
- `core/observability/`：日志、指标、追踪边界。
- `core/utils/`：稳定共享工具边界。
- `ai_runtime/`：根级 AI Runtime 蓝图。
- `harness/runtime/`：Agent Runtime 蓝图。
- `harness/workflow/`：Workflow Execution 蓝图。
- `harness/memory/`：Memory 蓝图。
- `harness/files/`：文件处理蓝图。
- `harness/multimodal/`：多模态蓝图占位。
- `harness/policies/`：策略和治理蓝图。
- `harness/events/`：事件协议蓝图。
- `schemas/`：Schema 草案位置。
- `evals/`：评测资产位置。
- `infra/`：基础设施说明位置。

## 设计原则

- 模板核心保持业务无关。
- 可运行代码不因目录对齐而移动。
- 当前能力和未来蓝图必须明确区分。
- 新目录默认只放 README 或占位文件。
- 任何具体业务逻辑都应放在独立模块中，而不是底座核心。

## 当前不包含

- 真实外部模型主链路依赖。
- embedding provider。
- 向量数据库。
- 多模态处理。
- Human Review 逻辑。
- 生产级权限系统。
- Eval Runner。
- 复杂 workflow planner。
