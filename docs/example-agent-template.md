# Example Agent Template 示例模板

V0.6.3 新增业务无关的 example agent template `generic_agent`。

## 设计目标

- 展示完整的 agent.json 结构和字段用法
- 可作为创建新 Agent 的参考起点
- 不是业务 Agent，不包含任何行业特定逻辑

## generic_agent 结构

```json
{
  "id": "generic_agent",
  "name": "Generic Agent",
  "description": "Business-neutral example agent template...",
  "version": "0.1.0",
  "runtime_version": "v0.6.3",
  "provider": {
    "provider_name": "mock",
    "model": "mock",
    "config_ref": "default"
  },
  "tools": {
    "allowed_tools": ["mock_echo"],
    "required_tools": []
  },
  "rag": {
    "enabled": false,
    "collection": "default",
    "retrieval_mode": "keyword"
  },
  "workflow": {
    "entrypoint": "modules.demo_agent.agent:execute",
    "nodes": ["input_node", "provider_node", "tool_node", "final_node"],
    "edges": [["input_node", "provider_node"], ["provider_node", "tool_node"], ["tool_node", "final_node"]]
  },
  "eval": {
    "cases_path": "evals/cases/",
    "required_checks": ["status", "events", "timeline"]
  },
  "policies": [],
  "guardrails": [],
  "metadata": {
    "author": "Agent Harness Template",
    "tags": ["business-neutral", "reference", "scaffold"],
    "purpose": "Developer reference example — not a business agent"
  }
}
```

## 接入现有 loader / registry

`generic_agent` 位于 `templates/agent-template/agent.json`，与 V0.6.0–0.6.1
的 loader 路径兼容。API 查询方式：

| API | 响应 | 说明 |
|---|---|---|
| `GET /api/agent-templates` | `list[TemplateSummary]` | 列表含 generic_agent |
| `GET /api/agent-templates/generic_agent` | `AgentTemplate` | 简化视图 |
| `GET /api/agent-templates/generic_agent/config` | `AgentConfig` | 完整嵌套配置 |
| `GET /api/agent-templates/generic_agent/validate` | `ValidateResult` | 校验结果 |

## 创建新 Agent

1. 复制 `templates/agent-template/` 到新目录
2. 修改 `agent.json`（id / name / provider / tools 等）
3. 重启 API 后通过 `GET /api/agent-templates/{id}` 验证
