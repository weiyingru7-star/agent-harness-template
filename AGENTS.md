# Agent Development Rules 智能开发规则

本仓库是一个**业务无关的通用 Agent Harness 模板**。它未来会支持多种可复用 Agent 应用，但当前实现必须严格限制在已批准的阶段范围内。

## Project Goal 项目目标

构建一个可复用、业务无关的 AI Agent 应用底座。模板核心不绑定任何具体行业，也不提前假设未来业务形态。

未来模板会逐步支持 agent runtime、ai runtime、skill registry、tool registry、state machine、memory、RAG、file processing、multimodal input、workflow execution、human review、observability 和 evals。除非当前任务明确授权，否则这些都属于未来阶段能力，不允许提前实现。

## Business-Agnostic Principle 业务无关原则

`agent-harness-template` 是通用 Agent 底座，核心代码、核心文档、默认页面和 `demo_agent` 不允许绑定任何具体行业。

禁止在模板核心中写死具体行业、业务场景或领域实体名称。具体行业只能出现在 `modules/xxx_agent` 业务模块中。

如需示例，只能使用中性表达，例如：文档助手、流程助手、分析助手。

## Current Stage 当前阶段

当前阶段：V0.3.7 Tool Runtime documentation consolidated。

已完成的通用底座能力：
- Agent Runtime（V0.2.x）：Trace / Span、Checkpoint、Failure / Retry、Timeline、Eval Trajectory
- Tool Runtime（V0.3.x）：Tool Call Contract、参数校验、结果标准化、超时控制、重试、权限校验、沙箱策略、文档收口

下一阶段规划：V0.4.0 RAG Pipeline 增强。

## Forbidden Scope 禁止提前实现

除非用户明确批准，否则不要实现或创建以下内容：

- 业务 Agent（电商、客服、服装等具体行业）
- 真实外部模型 provider（保持 mock 默认）
- 真实向量数据库（V0.4.0 以前）
- 真实 embedding provider
- 多租户、权限系统、多模态
- 复杂异步队列、外部 sandbox
- 改现有 API 路径或响应结构

## File Modification Rules 文件修改规则

- 只修改当前用户任务直接相关的文件。
- 不要修改与当前任务无关的文件。
- 不要做大范围重构。
- 未经用户明确要求，不要删除已有功能。
- 除非任务需要，不要重命名文件或目录。
- 不要把业务专用代码写进模板核心。
- 不要提交密钥、真实凭据或敏感信息。

## Required Work Process 必须遵守的工作流程

每次修改文件前，必须先说明：

- 准备创建或修改哪些文件。
- 为什么这些文件属于当前任务范围。
- 如果任务范围不清楚，必须先提问。

每次修改文件后，必须说明：

- 创建或修改了哪些文件。
- 每个文件大致改了什么。
- 应该运行哪些验收命令。
- 哪些测试没有运行，以及原因。

## Uncertainty Rule 不确定时的规则

如果需求有冲突、信息不完整，或存在多种理解方式，必须先问用户，不要猜测，也不要擅自实现未来阶段功能。

## Commands 常用命令

- 安装后端依赖：`make install-api`
- 安装前端依赖：`make install-web`
- 安装全部依赖：`make install`
- 启动后端：`make dev-api`
- 启动前端：`make dev-web`
- 运行后端测试：`make test-api`
- 启动基础设施：`make up`
- 停止基础设施：`make down`
