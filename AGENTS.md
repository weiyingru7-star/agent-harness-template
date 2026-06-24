# Agent Development Rules 智能开发规则

本仓库是一个**业务无关的通用 Agent Harness 模板**。它未来会支持多种可复用 Agent 应用，但当前实现必须严格限制在已批准的阶段范围内。

## Project Goal 项目目标

构建一个可复用、业务无关的 AI Agent 应用底座。模板核心不绑定任何具体行业，也不提前假设未来业务形态。

未来模板会逐步支持 agent runtime、ai runtime、skill registry、tool registry、state machine、memory、RAG、file processing、multimodal input、workflow execution、human review、observability 和 evals。除非当前任务明确授权，否则这些都属于未来阶段能力，不允许提前实现。

## Current Stage 当前阶段

当前阶段：Stage 1。

Stage 1 只允许包含：

- Next.js 前端首页
- FastAPI 后端 `/health`
- PostgreSQL 和 Redis 的 Docker Compose 配置
- `.env.example`
- Makefile
- README
- AI 开发约束文档
- 后端基础健康检查测试

## Forbidden Scope 禁止提前实现

除非用户明确批准进入对应阶段，否则不要实现或创建以下内容：

- Agent runtime
- Run、Step、Event、Task、Artifact 数据模型
- AI Runtime 或模型 provider
- Skill registry
- Tool registry
- State machine
- Memory
- RAG
- File upload 或 file processing
- Multimodal processing
- Workflow execution
- Human review
- Observability dashboards
- Evals
- Business modules
- Stage 2-5 目录或占位实现

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
