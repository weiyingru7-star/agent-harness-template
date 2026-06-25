# Tool Timeout 工具超时

V0.3.3 为 Tool 系统增加最小 `timeout_ms` 能力。每个 tool 可以配置超时时间，工具执行超过限制时，记录 `tool_call failed`、`ToolTimeoutError`、`tool.call.failed` event，并在 timeline/eval 中可见。

## 设计目标

- 工具级超时控制，以毫秒为单位配置。
- 超时是 tool 调用失败，不是 run 失败。run 仍 `completed`。
- 基于 `threading.Thread`（daemon）+ `join(timeout)` 实现，纯标准库，无外部依赖。
- `timeout_ms=None` 时行为与 V0.3.2 完全一致（无超时、零额外开销）。

## ToolDefinition.timeout_ms

```python
class ToolDefinition(BaseModel):
    ...
    timeout_ms: int | None = None  # 新增
```

- `None` 或 `<=0` = 无超时限制（原 V0.3.2 行为）
- `> 0` = 工具执行的最大毫秒数

`mock_echo` 配置了 `timeout_ms=1000`（1 秒超时）。

## execute_with_timeout

`apps/api/app/registries/tool_timeout.py`：

```python
def execute_with_timeout(handler, args, timeout_ms=None) -> ToolResult:
```

核心实现：
1. `timeout_ms = None` → 直接调用 handler，返回 ToolResult。
2. `timeout_ms > 0` → 在 daemon 线程中执行 handler，主线程 `join(timeout_ms/1000)`。
3. 线程未完成 → 返回 `ToolResult(status="failed", error_type="ToolTimeoutError")`。
4. 线程完成但有异常 → 返回 `ToolResult(status="failed", error_type="ToolExecutionError")`。
5. 线程正常完成 → 返回 handler 的 ToolResult。

函数永不抛出异常——超时和异常都封装为 `ToolResult` 返回。

## 超时时的记录

| 项目 | 值 |
|---|---|
| ToolCall.status | `"failed"` |
| ToolCall.error_type | `"ToolTimeoutError"` |
| ToolCall.error_message | `"Tool timed out after 1000ms"` |
| ToolCall.result.status | `"failed"` |
| ToolCall.result.error_type | `"ToolTimeoutError"` |
| ToolCall.result.metadata.timeout_ms | 配置的超时值 |
| event | `tool.call.failed`（metadata 含 timeout_ms/result_status/error_type） |

## `__slow_tool__` 触发

### 完整链路

```
input 含 "__slow_tool__"
  → graph tool_node: 标记 intentional_slow_tool=True, tool_output=""
  → run_store _build_tool_arguments: 检测 marker → {"input": "__SLOW_TOOL__"}
  → ToolArgsValidator: 校验通过 (input 是 string)
  → execute_with_timeout(handler, args, timeout_ms=1000)
    → daemon 线程: mock_echo({"input": "__SLOW_TOOL__"})
    → mock_echo: 检测 "__SLOW_TOOL__" → time.sleep(10)
    → join(1.0) 返回 (超时)
  → run_store: tool_call(status=failed, error_type=ToolTimeoutError)
  → event: tool.call.failed
  → run: 仍 completed
```

## Events / Timeline / Eval 兼容

- `tool.call.started` 保留不变。
- `tool.call.completed` 成功路径不变。
- `tool.call.failed` 的 metadata 根据失败原因动态包含 `timeout_ms`。
- timeline 透传 `tool_call.error_type`/`error_message`，超时时显示 `ToolTimeoutError`。
- eval case 新增 `demo_agent_tool_timeout.json`。原 4 个 case 不变。

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
