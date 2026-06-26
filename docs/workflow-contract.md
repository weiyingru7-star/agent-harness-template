# Workflow Contract 工作流合同

V0.7.0 定义业务无关的 Workflow Contract，让 agent.yaml 中的 workflow 可以声明 nodes、edges、entrypoint、terminal nodes、node types。

## 设计目标

- 定义标准化 workflow node / edge / condition 合同
- 提供 WorkflowValidator 校验结构完整性
- 接入 AgentTemplateRegistry.validate_template()
- 不执行 workflow，不调用 provider/tool/rag

## WorkflowNode

```python
class WorkflowNode(BaseModel):
    id: str                    # 节点唯一标识
    type: str                  # input / provider / tool / rag / decision / final
    name: str | None = None
    config: dict = {}
    next: list[str] = []       # 后续节点 id
    metadata: dict = {}
```

## WorkflowEdge

```python
class WorkflowEdge(BaseModel):
    from_node: str             # 起点节点 id（JSON 中用 "from"）
    to: str                    # 终点节点 id
    condition: WorkflowCondition | None = None
    metadata: dict = {}
```

## WorkflowCondition

```python
class WorkflowCondition(BaseModel):
    type: str = "always"       # always / expression / route
    expression: str | None = None
    route_key: str | None = None
```

不执行 expression，只做结构校验。

## 校验规则

| 规则 | 失败时 error |
|---|---|
| entrypoint 引用已有 node id | entrypoint not found in nodes |
| node id 唯一 | duplicate node id |
| edge from/to 引用已有 node id | edge references unknown node |
| edge 不是自环 | self-loop |
| terminal_nodes 引用已有 node id | terminal_nodes includes unknown node |
| node type 在允许列表中 | unsupported node type |

## 与 AgentTemplate 集成

`GET /api/agent-templates/{id}/validate` 现在返回 workflow 校验结果。

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

## 文件

- `apps/api/app/registries/workflow_validator.py`：WorkflowNode / WorkflowEdge / WorkflowCondition / WorkflowValidator
- `schemas/workflow.schema.json`：增强后的 JSON Schema
- `templates/agent-template/agent.json`：含 `terminal_nodes` 示例
