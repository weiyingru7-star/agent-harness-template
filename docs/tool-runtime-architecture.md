# Tool Runtime Architecture 工具执行架构

V0.3.0–V0.3.6 构建了一个完整的 Tool Runtime 执行栈。本文档用文本架构图说明每层的位置和职责。

## Agent Run → Step 视图

```
Agent Run
  └─ Step: input_node
  └─ Step: skill_node
  └─ Step: tool_node               ← Tool Runtime Layer
       │
       ├─ 1. tool.call.started     event
       ├─ 2. Permission Check      检查 tool 的 permission_level
       ├─ 3. Sandbox Check         检查 tool 的 execution_mode
       ├─ 4. Args Validation       根据 args_schema 校验参数
       ├─ 5. Timeout / Retry       execute_with_retry 循环
       │    ├─ Attempt 1           execute_with_timeout
       │    ├─ (retry_scheduled     event, if retryable)
       │    └─ Attempt N           execute_with_timeout
       ├─ 6. Tool Execution        工具函数被实际调用
       ├─ 7. ToolResult            标准化返回结构
       ├─ 8. tool.call.completed   或 tool.call.failed event
       ├─ 9. ToolCall Record       持久化到 tool_calls 表
       └─ 10. Timeline / Eval      timeline item + eval 断言
  └─ Step: final_node
```

执行顺序（决策理由）：permission 最轻量，先拒绝无效调用；sandbox 次之，检查执行可行性；args 校验需要实际参数（build_tool_arguments 在 sandbox 之前已构造）；timeout 包裹执行；retry 包裹 timeout+执行。

## 分层职责

| 层 | 版本 | 模块 | 职责 | 拒绝时行为 |
|---|---|---|---|---|
| Tool Call Contract | V0.3.0 | models/run.py+repositories | ToolCall 模型、持久化、API 路由 | — |
| Args Validation | V0.3.1 | tool_args.py+ToolArgsValidator | 根据 args_schema 校验参数 | tool.call.failed, 不执行 tool |
| Tool Result | V0.3.2 | tool_result.py+ToolResult | 成功/失败的统一结构 | — |
| Timeout | V0.3.3 | tool_timeout.py+execute_with_timeout | daemon thread 超时控制 | ToolTimeoutError, tool.call.failed |
| Retry | V0.3.4 | tool_retry.py+execute_with_retry | 失败重试循环 | 耗尽 attempts 后最终失败 |
| Permission | V0.3.5 | tool_permission.py+ToolPermissionChecker | permission_level 校验 | ToolPermissionDenied, tool.call.failed |
| Sandbox | V0.3.6 | tool_sandbox.py+ToolSandboxChecker | execution_mode 检查 | ToolSandboxViolation, tool.call.failed |

## 数据流

```
ToolDefinition (工具注册表)
  ├─ args_schema        → ToolArgsValidator
  ├─ timeout_ms         → execute_with_timeout
  ├─ max_attempts / retry_on_error_types → execute_with_retry
  ├─ permission_level   → ToolPermissionChecker
  └─ execution_mode     → ToolSandboxChecker

ToolCall (记录结果)
  ├─ status: completed / failed
  ├─ result: ToolResult (标准化 dict)
  ├─ error_type / error_message (失败时)
  ├─ metadata.attempts (重试时)
  └─ metadata.retry_count / final_attempt_status
```

## 相关文档

- [Tool Runtime 总入口](tool-runtime.md)
- [错误类型参考](tool-runtime-errors.md)
- [Eval Cases 说明](tool-runtime-eval.md)
- [Tool Call Contract](tool-call-contract.md)
- [Tool Args Schema](tool-args-schema.md)
- [Tool Result Contract](tool-result-contract.md)
- [Tool Timeout](tool-timeout.md)
- [Tool Retry](tool-retry.md)
- [Tool Permission](tool-permission.md)
- [Tool Sandbox](tool-sandbox.md)
