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

当前阶段：V1.4 RAG Tenant Filter。

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
- Policy Dry-Run Evaluator（V0.8.4）：PolicyDryRunEvaluator——根据 Policy/Guardrail/Context 生成 DecisionResult。支持 always/match/route condition，expression 安全拒绝。不接 runtime，不拦截请求
- Guardrail Runtime Integration Plan（V0.8.5）：集成计划文档，设计 runtime 接入点、execution mode、dry-run/enforcement 边界。不修改任何代码
- Input Guardrail Dry-Run Hook（V0.8.6）：run_input_guardrail() 在 RunStore._create_run 中插入 input dry-run hook。构造 input-scope EvaluationContext，调用 PolicyDryRunEvaluator，记录 guardrail.dry_run.completed event。纯 dry-run，不拦截请求
- Tool Guardrail Dry-Run Hook（V0.8.7）：run_tool_guardrail() 在 ToolExecutionPipeline._execute_tool 中插入 tool dry-run hook。构造 tool-scope EvaluationContext，记录 guardrail event。纯 dry-run，不阻止 tool 执行
- Provider / RAG Guardrail Dry-Run Helpers（V0.8.8）：run_provider_guardrail() / run_rag_guardrail() dry-run helpers。返回 DecisionResult dict。当前不做 runtime wiring——provider/rag runtime 没有 run_id/trace_id/event_repository 上下文。纯 helper，不接入运行链路
- Policy / Guardrail Runtime Docs Consolidation（V0.8.9）：V0.8 全阶段文档收口，整理 support/not-supported 说明。不修改代码
- CLI / Scaffold Contract（V0.9.0）：设计 CLI / Scaffold 方案，新增 docs/cli-scaffold-contract.md。覆盖命令设计、scaffold 生成物、命名规则、安全规则、V0.9 路线图。只做 contract 文档
- Scaffold Module Script（V0.9.1）：scripts/scaffold_module.py，支持 --name/--dry-run/--force/--preview。命名校验、sensitive name 拒绝、path traversal 拒绝、business term 检查。复用 templates/module-template/。22 条测试
- Scaffold Agent Template（V0.9.2）：scripts/scaffold_agent.py，从 templates/agent-template/ 读取源模板，生成 templates/<name>/ 下的 agent.json + README.md。生成的 agent.json 可被 AgentConfig 和 AgentTemplateRegistry 解析。复用命名校验。10 条测试
- Scaffold Eval Cases（V0.9.3）：scripts/scaffold_eval.py，生成 evals/cases/<name>.json，匹配 run_evals.py 的 13 个 REQUIRED_FIELDS 和 eval-case.schema.json。使用 demo_agent module。复用命名校验。测试包含 JSON 结构校验和可选 schema 校验
- Scaffold Docs Generator（V0.9.4）：scripts/scaffold_docs.py，生成 docs/scaffolds/<kind>-<name>.md。支持 --kind (module/agent/eval/generic)。每个 kind 生成不同的中性文档骨架。复用命名校验。27 条测试
- CLI Validation and Hygiene（V0.9.5）：抽取 scaffold 重复 validation 逻辑到 scripts/scaffold_validation.py。提供 validate_scaffold_name()、resolve_safe_target()、format_errors()。4 个 scaffold 脚本统一引用。59 条共享校验测试
- CLI Docs Consolidation（V0.9.6）：V0.9 全阶段文档收口。新增 cli-scaffold-guide.md、cli-scaffold-troubleshooting.md。不修改代码
- Minimal Reusable Agent Harness Template（V1.0）：新增 QUICKSTART.md、TEMPLATE_USAGE.md、release-checklist.md、check_template_health.py。README 重新定位为 template landing page。不修改 runtime
- Multi-user Runtime Contract（V1.1）：UserContext / Conversation / Message / RunBinding 数据合同。CreateRunRequest 可选 user_id/tenant_id/conversation_id/message_id。20 条 contract + API 测试。不修改 runtime 行为
- Message / Conversation API（V1.2）：实现 Conversation/Message CRUD API 和 conversation-triggered run。新增 ConversationRecord/MessageRecord 表（自动创建）。assistant message 在 run completed 且有 output 时回写。旧 /api/runs 完全不变。21 条测试
- Tenant Isolation（V1.3）：conversation/message API 强制 tenant_id。缺失→400，不匹配→404。list conversations 必须 tenant-scoped。user_id 一致性校验。旧 /api/runs 不变
- RAG Tenant Filter（V1.4）：RAG ingestion/retrieval 支持可选 tenant_id。存储在已有 metadata JSON 列（无迁移）。keyword/vector/hybrid 三种模式均支持 tenant 过滤。向后兼容旧无 tenant 文档

下一阶段规划：V1.5 Tool Permission / Ownership Guard。

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
