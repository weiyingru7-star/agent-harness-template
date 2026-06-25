# Tool Result Contract 工具结果标准化

V0.3.2 为 Tool 系统增加标准化 `ToolResult` Contract。每次工具执行后，不管成功还是失败，都返回统一结构，便于 trace、timeline、eval 和后续 tool retry / timeout / permission / sandbox 扩展。

## 设计目标

- 所有工具返回统一结果结构，成功/失败路径都有标准字段。
- `ToolResult` 由工具函数返回，`RunStore` 的 `tool_node` 分支将其序列化为 `ToolCall.result`。
- 工具执行抛异常时被 `RunStore` 捕获，记录 `failed` tool_call 和 `tool.call.failed` event。
- 校验失败路径（V0.3.1）的 result 也从 `{}` 改为标准 `ToolResult` 结构。

## ToolResult 模型

`apps/api/app/registries/tool_result.py`：

```python
class ToolResult(BaseModel):
    status: ToolResultStatus  # "completed" | "failed"
    output: str | None = None
    raw_output: Any = None
    summary: str | None = None
    artifacts: list[dict] = []
    metadata: dict = {}
    error_type: str | None = None
    error_message: str | None = None
```

## ToolCall.result 标准结构

### 成功时

```json
{
  "status": "completed",
  "output": "Mock tool echo: hello",
  "raw_output": "Mock tool echo: hello",
  "summary": "Echoed: 'hello'",
  "artifacts": [],
  "metadata": {"char_count": 5},
  "error_type": null,
  "error_message": null
}
```

### 校验失败时

```json
{
  "status": "failed",
  "output": null,
  "summary": null,
  "error_type": "ToolArgsValidationError",
  "error_message": "wrong_type: input expected string, got integer"
}
```

### 工具异常时

```json
{
  "status": "failed",
  "output": null,
  "summary": null,
  "error_type": "ToolExecutionError",
  "error_message": "RuntimeError: mock_echo intentional exception for test"
}
```

结果存储在数据库 `tool_calls.result` JSON 列中，不改变表结构。

## 三种路径

| 路径 | 触发 | tool_call.status | result.status | event |
|---|---|---|---|---|
| 正常 | `"hello"`（默认） | `completed` | `completed` | `tool.call.completed`（metadata 含 result_status/summary） |
| 参数校验失败 | `__invalid_tool_args__` | `failed` | `failed` | `tool.call.failed` |
| 工具执行异常 | `__tool_exception__` | `failed` | `failed` | `tool.call.failed`（metadata 含 error_type/error_message） |

## Event 兼容

- `tool.call.completed`：metadata 新增 `result_status`、`summary` 字段。旧字段不变。
- `tool.call.failed`：metadata 新增 `result_status` 字段。旧字段不变。
- 不破坏已有 event_type。

## Timeline / Eval 兼容

- timeline 已透传 `tool_call.error_type`/`tool_call.error_message`，异常路径无需改装配代码。
- eval case 新增 `demo_agent_tool_exception.json`，覆盖工具异常轨迹。原 3 个 case 不变。

## demo_agent 触发词

| 触发词 | 效果 |
|---|---|
| （不填） | 正常执行，ToolResult.completed |
| `__invalid_tool_args__` | args 校验失败，ToolResult.failed |
| `__tool_exception__` | tool 内部抛异常，捕获后 ToolResult.failed |

graph 的 `tool_node` 只标记 `intentional_tool_exception: True`，run_store 据此构造 `{"input": "__TOOL_EXCEPTION__"}` 参数，args 校验通过后 `mock_echo` 检测到 `__TOOL_EXCEPTION__` 并 `raise RuntimeError`。

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
