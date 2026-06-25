# Tool Sandbox 安全执行

V0.3.6 为 Tool 系统增加最小 `execution_mode` 检查能力。运行前检查该 tool 是否允许在当前执行模式下运行。违反 sandbox_policy 时，不执行 tool，记录 `ToolSandboxViolation` 和 `tool.call.failed` event。

## 设计目标

- 最小安全执行层，在权限检查之后、参数校验之前执行。
- V0.3.6 只检查 `execution_mode` 级别。
- `sandbox_policy` 字段为 schema 完整性预留，V0.3.6 暂不深入检查。
- 不实现外部 sandbox、Docker、网络隔离或文件系统访问控制。

## ToolDefinition 字段

```python
class ToolDefinition(BaseModel):
    ...
    execution_mode: str = "in_process"      # "in_process" | "disabled" | "external_stub"
    sandbox_policy: dict | None = None
```

- `in_process`（默认）：V0.3.5 行为，正常执行
- `disabled`：禁止执行
- `external_stub`：预留，V0.3.6 视为 disabled

## ToolSandboxChecker

`apps/api/app/registries/tool_sandbox.py`：

```python
class ToolSandboxChecker:
    @staticmethod
    def check(tool_def, context_args=None) -> SandboxResult
```

- `execution_mode = "in_process"` → `allowed=True`
- `execution_mode = "disabled"` → `allowed=False, error_type=ToolSandboxViolation`

## 执行顺序

```
tool.call.started
  → permission check (V0.3.5)
  → sandbox check (V0.3.6, 新增)
  → args validation
  → timeout / retry / execution
```

sandbox 拒绝时：args validation 和 tool 执行**跳过**，不触发 retry。

## Sandbox 拒绝时的记录

| 项目 | 值 |
|---|---|
| ToolCall.status | `"failed"` |
| ToolCall.error_type | `"ToolSandboxViolation"` |
| ToolCall.result.status | `"failed"` |
| ToolCall.result.error_type | `"ToolSandboxViolation"` |
| ToolCall.result.metadata.execution_mode | `"disabled"` |
| event | `tool.call.failed`（metadata 含 execution_mode / result_status） |

## 触发词

| 触发词 | 效果 |
|---|---|
| `__sandbox_blocked__` | 模拟 tool execution_mode=disabled，被 sandbox 拒绝 |

## Events / Timeline / Eval 兼容

- `tool.call.started` 保留
- `tool.call.completed` 保留（正常路径）
- `tool.call.failed` metadata 新增 `execution_mode` 字段
- 拒绝时不触发 retry
- timeline 通过 ToolCall.metadata 见 sandbox 拒绝信息
- eval case 新增 `demo_agent_tool_sandbox_blocked.json`

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
