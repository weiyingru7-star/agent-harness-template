# Workflow Validation / Eval 工作流校验

V0.7.3 为 workflow 增加标准化 validation result 和最小 eval 能力。

## ValidationErrorItem

```python
class ValidationErrorItem(BaseModel):
    code: str                    # 错误代码
    message: str                 # 可读消息
    path: str | None = None      # 可选，错误位置
    severity: str = "error"      # "error" | "warning"
```

## Error Codes

| Code | 含义 | Severity |
|---|---|---|
| WORKFLOW_ENTRYPOINT_MISSING | entrypoint 引用不存在节点 | error |
| WORKFLOW_NODE_DUPLICATE | 节点 id 重复 | error |
| WORKFLOW_NODE_TYPE_UNSUPPORTED | 不支持的 node type | error |
| WORKFLOW_EDGE_TARGET_NOT_FOUND | edge 引用不存在节点 | error |
| WORKFLOW_SELF_LOOP | edge 自环 | error |
| WORKFLOW_TERMINAL_NODE_NOT_FOUND | terminal_node 不存在 | error |
| WORKFLOW_RAG_RETRIEVAL_MODE_INVALID | rag retrieval_mode 非法 | warning |
| WORKFLOW_CONDITION_TYPE_UNSUPPORTED | condition type 非法 | warning |
| WORKFLOW_CONFIG_KEY_UNKNOWN | config key 不在白名单 | warning |
| WORKFLOW_EXPECTED_OUTPUT_MISSING | 缺少预期 output | warning |
| WORKFLOW_DECISION_ROUTE_NOT_FOUND | decision route 目标不存在 | warning |

## WorkflowValidationResult

```python
class WorkflowValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []              # 字符串错误列表（兼容）
    warnings: list[str] = []            # 字符串警告列表（兼容）
    error_items: list[ValidationErrorItem] = []  # 结构化错误
```

## Workflow Eval

运行方式：

```bash
python3 scripts/run_workflow_evals.py
```

### Case 格式

```json
{
  "id": "valid_workflow",
  "name": "Valid Workflow",
  "workflow": { ... },
  "expected_valid": true,
  "expected_error_codes": []
}
```

## 与 Agent Template 集成

- `get_template()` 返回的 AgentTemplate.config 中保留完整 workflow 结构
- `validate_template()` 的 ValidateResult 中 error_items 包含 workflow 校验结果
