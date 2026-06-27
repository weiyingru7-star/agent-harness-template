# Claude Code Development Rules Claude Code 开发规则

本仓库是一个**业务无关的通用 Agent Harness 模板**。Claude Code 必须尊重当前阶段边界，不能提前实现未来阶段功能。

## Project Goal 项目目标

创建一个可复用的 AI Agent 应用模板，用来支持未来各种 Agent 项目，而不是绑定某一个具体业务。

未来阶段可以加入 agent runtime、ai runtime、registries、memory、RAG、files、workflows、human review、observability 和 evals。但除非当前任务明确要求，否则这些能力都不能提前加入。

## Business-Agnostic Principle 业务无关原则

`agent-harness-template` 是通用 Agent 底座，核心代码、核心文档、默认页面和 `demo_agent` 不允许绑定任何具体行业。

禁止在模板核心中写死具体行业、业务场景或领域实体名称。具体行业只能出现在 `modules/xxx_agent` 业务模块中。

如需示例，只能使用中性表达，例如：文档助手、流程助手、分析助手。

## Current Stage 当前阶段

当前阶段：V0.8.3 Guardrail Evaluation Context Contract。

已完成的通用底座能力：
- Agent Runtime（V0.2.x）：模块注册、执行契约、Trace / Span、Checkpoint、Failure / Retry、Timeline、Eval Trajectory
- Tool Runtime（V0.3.x）：Tool Call Contract、参数校验、结果标准化、超时控制、重试、权限校验、沙箱策略、文档收口
- RAG Runtime（V0.4.x）：Document/Chunk/Citation/RetrievalResult 合同、切分策略、直接文本创建、检索评估、嵌入层、向量存储、三种检索模式
- Provider Runtime（V0.5.x）：ProviderRequest/Response/Error 合同、smoke 对齐、streaming、fallback、timeout/retry、配置管理、真实模型适配
- Agent Template（V0.6.x）：AgentTemplate contract、嵌套配置、Registry API、TemplateSummary、ValidateResult、Example Agent Template
- Workflow Contract（V0.7.x）：WorkflowNode/Edge/Condition schema、WorkflowValidator、校验规则、built-in node contracts、validation error codes、eval runner、文档收口
- Tool Pipeline Refactor（V0.7.6）：从 RunStore 抽取 Tool Execution Pipeline 到独立 tool_runtime 模块
- Provider Consolidation（V0.7.7）：收口 provider_runtime（canonical）和 ai_runtime（legacy）的边界
- Policy / Guardrail Contract（V0.8.0）：Policy / Guardrail / Rule / Condition 合同、JSON Schema、PolicyValidator、AgentTemplate 集成。只做 contract / schema / validator / docs / tests，不执行 policy
- Policy Validation Evals（V0.8.1）：独立 policy validation eval runner（scripts/run_policy_evals.py），7 个 eval case，补齐稳定 error codes。只验证 contract，不执行 policy
- Guardrail Decision Contract（V0.8.2）：GuardrailDecision / DecisionResult 合同、结构校验、JSON Schema、eval cases。只做 contract / schema / validator / docs / tests，不执行 policy
- Guardrail Evaluation Context Contract（V0.8.3）：EvaluationContext / EvaluationSubject 合同、结构校验、JSON Schema、eval cases、context_contract 类型 eval 支持。只做 contract，不执行 policy

下一阶段规划：V0.8.x Advanced Features / Agent Memory。

## Current Scope Constraints 当前修改约束

允许创建或修改：
- `apps/api/`：后端增量开发（不改现有 API 路径与响应契约）
- `apps/web/`：前端增量开发（不删已有页面）
- `core/`：共享基础设施（改 db 需谨慎）
- `harness/`：蓝图目录（多数为 README 占位）
- `modules/`：中性示例模块（不创建业务 Agent）
- `schemas/`：JSON Schema 维护
- `evals/`、`scripts/`、`cli/`、`docs/`：辅助工具与文档

禁止提前实现：
- 业务 Agent（电商、客服、服装等具体行业）
- 真实外部模型 provider（保持 mock 默认）
- 真实向量数据库（V0.4.0 以前）
- 真实 embedding provider
- 多租户、权限系统、多模态
- 复杂异步队列、外部 sandbox
- 改现有 API 路径或响应结构

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

## Commands 常用命令

- `make install-api`
- `make install-web`
- `make install`
- `make dev-api`
- `make dev-web`
- `make test-api`
- `make up`
- `make down`
