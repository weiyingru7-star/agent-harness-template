# Tool Permission 工具权限

V0.3.5 为 Tool 系统增加最小权限校验能力。工具执行前检查权限，拒绝时记录 `ToolPermissionDenied` 和 `tool.call.failed` event。

## 设计目标

- 工具执行前权限校验，拒绝时不执行 tool。
- 不实现人工审批、RBAC、多租户。
- 三个权限级别：safe（允许）、restricted（需 context）、blocked（拒绝）。

## ToolDefinition 字段

```python
class ToolDefinition(BaseModel):
    ...
    permission_level: str = "safe"         # "safe" | "restricted" | "blocked"
    allowed_contexts: list[str] | None = None  # restricted 时允许的 context
    requires_approval: bool = False             # 预留
```

## ToolPermissionChecker

`apps/api/app/registries/tool_permission.py`：

```python
class ToolPermissionChecker:
    @staticmethod
    def check(tool_def, run_context=None) -> PermissionResult
```

- `safe` → 总是允许
- `restricted` → 仅当 `run_context in allowed_contexts` 时允许
- `blocked` → 总是拒绝

## 执行顺序

```
tool.call.started
  → 权限校验 (新增)
  → args validation
  → timeout / retry / execution
```

权限拒绝时：不经过 args validation、不执行 tool、不触发 retry。

## 权限拒绝时的记录

| 项目 | 值 |
|---|---|
| ToolCall.status | `"failed"` |
| ToolCall.error_type | `"ToolPermissionDenied"` |
| ToolCall.result.status | `"failed"` |
| ToolCall.result.error_type | `"ToolPermissionDenied"` |
| ToolCall.result.metadata.permission_level | `"restricted"` 或 `"blocked"` |
| event | `tool.call.failed`（metadata 含 permission_level / result_status） |

## 触发词

| 触发词 | 效果 |
|---|---|
| `__restricted_tool__` | 模拟 restricted tool，因 context 不匹配被拒绝 |
| `__blocked_tool__` | 模拟 blocked tool，永远被拒绝 |

## Events / Timeline / Eval 兼容

- `tool.call.started` 保留
- `tool.call.failed` metadata 含 `permission_level` 字段
- timeline 通过 ToolCall.metadata 见权限拒绝信息
- 拒绝时不触发 retry（retry_count/attempts 不存在）
- eval case 新增 `demo_agent_tool_permission_denied.json`

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
```
