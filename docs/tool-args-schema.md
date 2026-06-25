# Tool Args Schema 工具参数校验

V0.3.1 为 Tool 系统增加 `args_schema` 能力。每个 tool 可声明输入参数结构，`ToolArgsValidator` 在 tool 执行前做最小校验。校验失败时不执行 tool，记录 `tool.call.failed` event 和 `failed` 状态的 tool_call，但 run 仍然 `completed`。

## 设计目标

- 让每个 tool 的输入参数有显式契约。
- 在 tool 执行前拦截非法参数，避免 tool 收到意外输入。
- 校验失败是 tool 调用失败，不是 run 失败。run 是否 failed 仍由 V0.2.3 的 `__fail__` 路径负责。
- tool 的真实执行、参数校验、tool_call 记录统一收口在 `RunStore` 的 `tool_node` 分支，graph 不重复执行真实 tool。

## args_schema 结构

`ToolDefinition.args_schema` 是一个可选 JSON Schema 子集，挂载在工具注册表上：

```python
class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    args_schema: dict | None = None
```

最小支持的关键字（不实现完整 JSON Schema）：

| 关键字 | 说明 |
|---|---|
| `type` | 仅识别 `"object"`；非 object 视为不校验 |
| `required` | 字符串数组；缺失必填字段判失败 |
| `properties` | 字段级约束，每个字段只校验 `type` 与 `enum` |
| `properties.<k>.enum` | 枚举白名单 |
| `additionalProperties` | 设为 `false` 时禁止未声明字段 |

不支持的 JSON Schema 关键字：`oneOf`、`anyOf`、`allOf`、`$ref`、`pattern`、`format`、`minLength`、`maxLength`、`minimum`、`maximum` 等。出现这些关键字时校验器忽略，不报错。

`mock_echo` 的 args_schema：

```json
{
  "type": "object",
  "required": ["input"],
  "properties": {
    "input": {"type": "string"}
  }
}
```

## ToolArgsValidator

`apps/api/app/registries/tool_args.py`：

```python
class ToolArgsValidator:
    @staticmethod
    def validate(args: object, schema: dict | None) -> ArgsValidationResult
```

- `schema` 为 `None` 时直接通过，返回 `ArgsValidationResult(valid=True)`。
- `args` 不是 `dict` 时返回失败，`error.code = "args_not_object"`。
- 校验按 `required` → 字段 `type` → 字段 `enum` → `additionalProperties` 顺序收集所有错误，统一返回。
- 校验失败时 `error.code = "validation_failed"`，`error.message` 拼接所有错误细节，`details` 是错误列表。
- 纯标准库实现，不引入新依赖。

## 校验失败时的记录

`RunStore` 的 `tool_node` 分支统一负责 tool 执行、校验、tool_call 落库：

1. 写 `tool.call.started` event。
2. 构造 `arguments`，调用 `ToolArgsValidator.validate(arguments, tool_definition.args_schema)`。
3. 校验通过：执行 tool，写 `tool_call(status="completed")`，写 `tool.call.completed` event。
4. 校验失败：**不执行 tool**，写 `tool_call(status="failed", error_type="ToolArgsValidationError", error_message=..., result={})`，写 `tool.call.failed` event。

校验失败时的 tool_call 字段约定：

| 字段 | 值 |
|---|---|
| `status` | `"failed"` |
| `result` | `{}` |
| `error_type` | `"ToolArgsValidationError"` |
| `error_message` | 校验错误拼接串 |
| `metadata.args_validation_errors` | 错误明细列表 |

校验失败时的 events：

- `tool.call.started`（仍写）
- `tool.call.failed`（写，含 `error_type`/`error_message`/`args_validation_errors`）
- 不写 `tool.call.completed`

run 级别：校验失败时 run 仍 `completed`，`run.completed` 正常写入。

## demo_agent 触发 valid / invalid

demo_agent 的 graph 不再真实执行 tool，只保留状态流转和 node_trace。真实 tool 执行由 `RunStore` 的 `tool_node` 分支负责。

- 正常输入（如 `"hello"`）：graph 的 `tool_node` 产出占位 `tool_output = "tool pending execution"`，`RunStore` 构造 `arguments = {"input": skill_output}`，校验通过，执行 `mock_echo`，记录 `completed` tool_call。
- `__fail__` 输入：graph 的 `skill_node` 失败并 break，run failed，不到 tool_node，无 tool_call。
- `__invalid_tool_args__` 输入：graph 的 `tool_node` 标记 `intentional_invalid_args`，`RunStore` 构造 `arguments = {"input": 123}`（非字符串），校验失败，记录 `failed` tool_call，不执行 tool，run 仍 `completed`。

## timeline / eval 兼容

- timeline：`tool_node` 的时间线条目已透传 tool_call 的 `status`/`error_type`/`error_message`，failed tool_call 仍被创建，timeline 可见。
- trace：step 仍 `completed`，span 装配不受影响。
- eval：新增 `evals/cases/demo_agent_invalid_tool_args.json` 覆盖校验失败轨迹；原 `demo_agent_success` 和 `demo_agent_failure` 不变。

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
