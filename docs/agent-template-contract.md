# Agent Template Contract

V0.6.0 定义业务无关的 Agent Template Contract，让一个 Agent 可以通过 `agent.json` 声明它的基础信息、provider、tools、rag、workflow、eval 配置。

## 目标

- 定义标准化 agent template 合同
- 提供 loader 从 `agent.json` 读取和校验模板
- 提供 registry 列出和查询可用模板
- 不执行 Agent，不执行 provider/tool/rag

## AgentTemplate

```python
class AgentTemplate(BaseModel):
    id: str                # 必填，唯一标识
    name: str              # 必填，可读名称
    description: str = ""
    version: str = "0.1.0"
    provider: str = "mock"    # 默认 mock
    tools: list[str] = []
    rag_collection: str | None = None
    workflow: str = "default"
    eval_cases: list[str] = []
    metadata: dict = {}
```

## agent.json 示例

```json
{
  "id": "generic_agent",
  "name": "Generic Agent",
  "description": "Business-agnostic agent template for quick scaffolding.",
  "version": "0.1.0",
  "provider": "mock",
  "tools": ["mock_echo"],
  "rag_collection": "default",
  "workflow": "state_machine",
  "eval_cases": ["demo_agent_success", "demo_agent_invalid_tool_args"]
}
```

## AgentTemplateRegistry

```python
registry = AgentTemplateRegistry()
templates = registry.list_templates()   # list[AgentTemplate]
template = registry.get_template("generic_agent")  # AgentTemplate | None
```

loader 扫描 `templates/agent-template/` 目录下的 `agent.json` 文件。

## API

| 方法 | 路径 | 响应 | 用途 |
|---|---|---|---|
| GET | `/api/agent-templates` | `list[AgentTemplate]` | 列出所有可用模板 |
| GET | `/api/agent-templates/{template_id}` | `AgentTemplate` | 查询单个模板详情 |

## 创建新 Agent 模板

1. 在 `templates/agent-template/` 下创建 `<template_id>.json` 文件
2. 填写 `id` / `name` / `provider` / `tools` 等字段
3. 重启 API 或重新实例化 `AgentTemplateRegistry`
4. 通过 `GET /api/agent-templates/<template_id>` 验证

## 与已有 AgentManifest 的关系

| 组件 | 用途 | 位置 |
|---|---|---|
| `AgentManifest` | 模块扫描（module.yaml + agent.yaml） | `harness/registries/types.py` |
| `AgentTemplate` | 独立模板合同（standalone agent.json） | `app/registries/agent_template.py` |

`AgentTemplate` 更精简（无 `module_id` / `system_prompt_path`），新增 `rag_collection` / `eval_cases`。

## 验收

```bash
make test-api
curl -s http://localhost:8005/api/agent-templates
```
