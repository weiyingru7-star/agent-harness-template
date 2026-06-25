# Tool Runtime Errors 错误类型参考

V0.3.1–V0.3.6 定义了 5 种 tool 级错误类型。所有 tool 级错误都**不会导致 run failed**——run failed 只由 V0.2.3 的 `__fail__` 路径（skill_node 失败）触发。

## 错误对照表

| 错误类型 | ToolCall.status | ToolResult.status | event_type | run.status | 来源版本 |
|---|---|---|---|---|---|
| （无错误） | `completed` | `completed` | `tool.call.completed` | `completed` | V0.3.0 |
| ToolArgsValidationError | `failed` | `failed` | `tool.call.failed` | `completed` | V0.3.1 |
| ToolExecutionError | `failed` | `failed` | `tool.call.failed` | `completed` | V0.3.2 |
| ToolTimeoutError | `failed` | `failed` | `tool.call.failed` | `completed` | V0.3.3 |
| ToolPermissionDenied | `failed` | `failed` | `tool.call.failed` | `completed` | V0.3.5 |
| ToolSandboxViolation | `failed` | `failed` | `tool.call.failed` | `completed` | V0.3.6 |

## 各错误说明

### ToolArgsValidationError

- **触发条件**：tool 参数未通过 `args_schema` 校验（必填字段缺失、类型不匹配、枚举值不在白名单、额外属性被禁止）。
- **ToolCall.error_type**：`"ToolArgsValidationError"`
- **ToolCall.metadata.args_validation_errors**：校验失败明细列表。
- **工具是否执行**：否。
- **触发词**：`__invalid_tool_args__`。
- **详见**：[Tool Args Schema](tool-args-schema.md)

### ToolExecutionError

- **触发条件**：工具函数执行时抛出异常。
- **ToolCall.error_type**：`"ToolExecutionError"`
- **ToolCall.error_message**：`"{ExceptionType}: {exception_message}"`
- **工具是否执行**：是，执行未完成。
- **触发词**：`__tool_exception__`。
- **详见**：[Tool Result Contract](tool-result-contract.md)

### ToolTimeoutError

- **触发条件**：工具执行超过 `timeout_ms` 限制。
- **ToolCall.error_type**：`"ToolTimeoutError"`
- **ToolCall.error_message**：`"Tool timed out after {timeout_ms}ms"`
- **ToolCall.metadata.timeout_ms**：配置的超时值。
- **工具是否执行**：是，但在 daemon 线程中被超时遗弃。
- **触发词**：`__slow_tool__`。
- **详见**：[Tool Timeout](tool-timeout.md)

### ToolPermissionDenied

- **触发条件**：tool 的 `permission_level` 被设为 `restricted` 或 `blocked`，且当前 run context 未在 `allowed_contexts` 中（或被永久拒绝）。
- **ToolCall.error_type**：`"ToolPermissionDenied"`
- **ToolCall.result.metadata.permission_level**：被拒绝的级别。
- **工具是否执行**：否（在 args validation 之前拒绝）。
- **触发词**：`__restricted_tool__`、`__blocked_tool__`。
- **详见**：[Tool Permission](tool-permission.md)

### ToolSandboxViolation

- **触发条件**：tool 的 `execution_mode` 不是 `"in_process"`（`"disabled"` 或 `"external_stub"`）。
- **ToolCall.error_type**：`"ToolSandboxViolation"`
- **ToolCall.error_message**：`"Tool {tool_id} ({execution_mode}) execution not allowed"`
- **工具是否执行**：否（在 permission check 之后、args validation 之前拒绝）。
- **触发词**：`__sandbox_blocked__`。
- **详见**：[Tool Sandbox](tool-sandbox.md)

## Timeline 与错误

所有 tool 级错误都能在 timeline 中看到：

- **error_type**：通过 `timeline.item.metadata.error_type` 可见（由 `_build_step_timeline_item` 从 tool_call 的 error_type 透传）。
- **error_message**：通过 `timeline.item.metadata.error_message` 可见。
- **duration_ms**：失败的工具调用仍有 duration（从 started_at 到 ended_at）。

## 与 run 级别错误的关系

| 范围 | 错误源 | run.status | 触发方式 |
|---|---|---|---|
| Tool 级 | 5 种 tool 错误 | `completed` | `__invalid_tool_args__`/`__tool_exception__`/`__slow_tool__`/`__restricted_tool__`/`__sandbox_blocked__` |
| Run 级 | skill_node 失败 | `failed` | `__fail__`（V0.2.3） |

Tool 级错误**不**触发 `run.failed` event 或 run retry。run retry（V0.2.3 `/api/runs/{run_id}/retry`）只对 `run.status=failed` 的 run 生效。
