# Tool Retry 工具重试

V0.3.4 为 Tool 系统增加最小 retry 能力。工具调用失败时，可以按 `max_attempts` 重试。每次 attempt 都被记录到 ToolCall metadata 和 events 中。

## 设计目标

- 工具级 retry，不是 run retry。
- 每次 attempt 记录 attempt_index。
- 最终成功：ToolCall.status = completed。
- 最终失败：ToolCall.status = failed。
- 不实现复杂指数退避、异步队列或权限。

## ToolDefinition 字段

```python
class ToolDefinition(BaseModel):
    ...
    max_attempts: int = 1                              # 默认不重试
    retry_on_error_types: list[str] | None = None       # 默认不重试任何错误
```

- `max_attempts=1` = V0.3.3 行为（不重试）
- `retry_on_error_types=["ToolExecutionError"]` = 仅在工具执行异常时重试
- `retry_on_error_types=["ToolTimeoutError"]` = 仅在超时时重试
- 校验失败（ToolArgsValidationError）永不重试

## execute_with_retry

`apps/api/app/registries/tool_retry.py`：

```python
class RetryResult:
    final_result: ToolResult
    attempts: list[dict]    # each: attempt_index, status, error_type, error_message
    retry_count: int
    final_attempt_index: int
```

## retry 循环流程

```
tool.call.started
  → permission check (V0.3.5)
  → args validation
  → attempt 1 (execute_with_timeout)
      → 成功: tool.call.completed
      → 失败且可重试: tool.call.retry_scheduled → attempt 2
          → 成功: tool.call.completed
          → 失败且可重试: tool.call.retry_scheduled → attempt 3
              ...
              → 最终失败（不再重试或 attempt 用完）: tool.call.failed
```

## retry 时 ToolCall metadata

```json
{
  "attempts": [
    {"attempt_index": 1, "status": "failed", "error_type": "ToolExecutionError", ...},
    {"attempt_index": 2, "status": "completed", ...}
  ],
  "max_attempts": 2,
  "retry_count": 1,
  "final_attempt_status": "completed"
}
```

## 重试条件

```python
def _is_retryable(result, retry_on):
    if retry_on is None:
        return False
    return result.error_type in retry_on
```

## `__flaky_tool__` 触发

```
input 含 "__flaky_tool__"
  → graph: intentional_flaky_tool=True, tool_output=""
  → run_store: 覆写 max_attempts=2, retry_on=["ToolExecutionError"]
  → attempt 1: mock_echo 检测 __FLAKY_TOOL__ + attempt==1 → raise RuntimeError
  → retryable → emit tool.call.retry_scheduled
  → attempt 2: mock_echo 检测 __FLAKY_TOOL__ + attempt==2 → 正常执行
  → tool.call.completed, ToolCall(completed, retry_count=1)
  → run: 仍 completed
```

## Events / Timeline / Eval 兼容

- `tool.call.started` 保留
- `tool.call.retry_scheduled` 新增（仅在曾经 retry 时出现）
- `tool.call.completed` / `tool.call.failed` 保留，metadata 含 retry_count/max_attempts（仅在 retry 时出现）
- timeline 通过 ToolCall.metadata 见 retry 信息
- eval case 新增 demo_agent_flaky_tool_retry.json。原 5 个 case 不变。

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
