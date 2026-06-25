# Tool Runtime 工具执行运行时

V0.3.0–V0.3.6 构建了一个完整的 Tool Runtime 执行栈。本文档是整个 Tool Runtime 文档体系的总入口。

## 架构

详见 [Tool Runtime Architecture](tool-runtime-architecture.md)。

执行顺序：

```
tool.call.started
  → Permission Check (V0.3.5)
  → Sandbox Check (V0.3.6)
  → Args Validation (V0.3.1)
  → Timeout / Retry (V0.3.3 / V0.3.4)
  → Tool Execution
  → ToolResult (V0.3.2)
  → tool.call.completed / tool.call.failed (V0.3.0)
  → ToolCall Record
  → Timeline / Eval / Trace
```

## 文档体系

| 文档 | 说明 |
|---|---|
| [Tool Runtime Architecture](tool-runtime-architecture.md) | 执行链路架构图与分层说明 |
| [Tool Call Contract](tool-call-contract.md) | ToolCall 模型、事件、API 路由 |
| [Tool Args Schema](tool-args-schema.md) | args_schema 设计与 ToolArgsValidator |
| [Tool Result Contract](tool-result-contract.md) | ToolResult 模型与标准化结构 |
| [Tool Timeout](tool-timeout.md) | execute_with_timeout 设计与配置 |
| [Tool Retry](tool-retry.md) | execute_with_retry 与重试逻辑 |
| [Tool Permission](tool-permission.md) | ToolPermissionChecker 权限校验 |
| [Tool Sandbox](tool-sandbox.md) | ToolSandboxChecker 安全执行 |
| [Tool Runtime Errors](tool-runtime-errors.md) | 5 种错误类型对照表 |
| [Tool Runtime Eval](tool-runtime-eval.md) | 8 个 eval case 说明 |

## 验收

```bash
# 全量测试
make test-api

# Eval runner
python3 scripts/run_evals.py

# 业务词检查
python3 scripts/check_business_terms.py

# 前端构建
cd apps/web && npm run build
```

## 版本总览

| 版本 | 新增能力 | 关键模块 |
|---|---|---|
| V0.3.0 | ToolCall 记录与事件 | models/run.py, routes/tool_calls.py |
| V0.3.1 | args_schema 参数校验 | registries/tool_args.py |
| V0.3.2 | ToolResult 标准化 | registries/tool_result.py |
| V0.3.3 | timeout_ms 超时控制 | registries/tool_timeout.py |
| V0.3.4 | max_attempts 重试 | registries/tool_retry.py |
| V0.3.5 | permission_level 权限 | registries/tool_permission.py |
| V0.3.6 | execution_mode 沙箱 | registries/tool_sandbox.py |
