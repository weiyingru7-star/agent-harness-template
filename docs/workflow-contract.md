# Workflow Contract 工作流合同

V0.7.0–V0.7.3 构建了业务无关的 Workflow Contract 系统。当前只声明和校验结构，**不执行 workflow**，不调用真实 provider/tool/rag。

## 模块总览

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| Workflow Contract | V0.7.0 | WorkflowNode / Edge / Condition / Validator | 本文档 |
| Schema 增强 | V0.7.1 | description / inputs / outputs / condition types / config whitelist | 本文档 |
| Built-in Nodes | V0.7.2 | 6 种 node types + contract validation | [Built-in Nodes](workflow-built-in-nodes.md) |
| Validation / Eval | V0.7.3 | error codes + structured result + eval runner | [Validation](workflow-validation.md) |

## 架构

```
agent.json workflow section
  → WorkflowConfig (Pydantic)
    → WorkflowValidator.validate()
      → WorkflowValidationResult (errors + warnings + error_items)
        → error_items: list[ValidationErrorItem] (code/message/path/severity)
    → AgentTemplateRegistry.validate_template()
      → ValidateResult (含 workflow 校验结果)
    → GET /api/agent-templates/{id}/validate
```

## WorkflowNode

```python
class WorkflowNode(BaseModel):
    id: str
    type: str              # input / provider / tool / rag / decision / final
    name: str | None = None
    description: str | None = None      # V0.7.1
    config: dict = {}
    inputs: list[str] = []              # V0.7.1
    outputs: list[str] = []             # V0.7.1
    next: list[str] = []
    metadata: dict = {}
```

## WorkflowEdge

```python
class WorkflowEdge(BaseModel):
    id: str | None = None               # V0.7.1
    from_node: str = Field(alias="from")
    to: str
    condition: WorkflowCondition | None = None
    metadata: dict = {}
```

## WorkflowCondition

```python
class WorkflowCondition(BaseModel):
    type: str = "always"   # always / expression / route / on_success / on_failure
    expression: str | None = None
    route_key: str | None = None
    expected_value: str | None = None   # V0.7.1
    metadata: dict = {}
```

不执行 expression，只做结构校验。

## 校验规则

| 规则 | Error Code | Severity |
|---|---|---|
| entrypoint 引用已有 node id | WORKFLOW_ENTRYPOINT_MISSING | error |
| node id 唯一 | WORKFLOW_NODE_DUPLICATE | error |
| edge from/to 引用已有 node id | WORKFLOW_EDGE_TARGET_NOT_FOUND | error |
| edge 不是自环 | WORKFLOW_SELF_LOOP | error |
| terminal_nodes 引用已有 node id | WORKFLOW_TERMINAL_NODE_NOT_FOUND | error |
| node type 在允许列表中 | WORKFLOW_NODE_TYPE_UNSUPPORTED | error |
| config key 在白名单中 | WORKFLOW_CONFIG_KEY_UNKNOWN | warning |
| condition type 合法 | WORKFLOW_CONDITION_TYPE_UNSUPPORTED | warning |

完整错误代码见 [Workflow Validation](workflow-validation.md)。

## Built-in Node Contracts

6 种 node type 各有标准 config / inputs / outputs 定义：

| Type | config key | Expected Outputs |
|---|---|---|
| `input` | input_schema, default | payload |
| `provider` | provider_name, model, prompt_template, temperature | output, usage |
| `tool` | tool_name, args_template | result, status |
| `rag` | collection, retrieval_mode, query_template, limit | results, citations |
| `decision` | routes, default_route | selected_route |
| `final` | output_template | final_output |

详见 [Built-in Workflow Nodes](workflow-built-in-nodes.md)。

## 与 AgentTemplate 集成

`GET /api/agent-templates/{id}/validate` 返回 workflow 校验结果：

```json
{
  "template_id": "generic_agent",
  "valid": true,
  "errors": [],
  "warnings": [],
  "checked_at": "...",
  "metadata": {}
}
```

## 边界说明

- 当前**不执行** workflow
- 当前**不执行** provider / tool / rag 节点
- 当前**不是**完整 workflow engine
- `scripts/run_workflow_evals.py` 只评估 validation，不执行节点
- V0.8.x 才进入 Policy / Guardrail Runtime

## 文件

- `apps/api/app/registries/workflow_validator.py`：模型 + validator
- `schemas/workflow.schema.json`：JSON Schema
- `templates/agent-template/agent.json`：generic_agent 示例
- `evals/workflow_cases/`：eval cases
- `scripts/run_workflow_evals.py`：workflow eval runner
