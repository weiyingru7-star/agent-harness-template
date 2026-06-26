# Agent Template Registry API

V0.6.2 增强 Agent Template Registry API，返回结构化响应，包含 TemplateSummary 和 ValidateResult。

## API 路径

| 方法 | 路径 | 响应 | 用途 |
|---|---|---|---|
| GET | `/api/agent-templates` | `list[TemplateSummary]` | 列表视图（含计算字段） |
| GET | `/api/agent-templates/{id}` | `AgentTemplate` | 简化视图 |
| GET | `/api/agent-templates/{id}/config` | `AgentConfig` | 完整嵌套配置 |
| GET | `/api/agent-templates/{id}/validate` | `ValidateResult` | 结构化校验结果 |

## TemplateSummary

列表响应包含已计算的摘要字段：

```json
{
  "id": "generic_agent",
  "name": "Generic Agent",
  "description": "...",
  "version": "0.1.0",
  "runtime_version": "v0.6.1",
  "provider_name": "mock",
  "tools_count": 1,
  "rag_enabled": false,
  "workflow_type": "modules.demo_agent.agent:execute",
  "nodes_count": 4,
  "eval_cases_path": "evals/cases/",
  "metadata": {}
}
```

## ValidateResult

校验端点返回结构化结果：

```json
{
  "template_id": "generic_agent",
  "valid": true,
  "errors": [],
  "warnings": [],
  "checked_at": "2026-06-26T12:00:00+00:00",
  "metadata": {}
}
```

失败时：

```json
{
  "template_id": "unknown_template",
  "valid": false,
  "errors": ["Template not found: unknown_template"],
  "warnings": [],
  "checked_at": "...",
  "metadata": {}
}
```

## 错误处理

- template 不存在 → GET `/{id}`、`/{id}/config` → 404
- template 不存在 → `/{id}/validate` → 200 + `valid=false` 错误信息
- JSON 解析失败 → `_load_config` 捕获并跳过（registry 启动时 warning）

## 验收

```bash
curl -s http://localhost:8005/api/agent-templates | python3 -c "
import json,sys;ts=json.load(sys.stdin)
for t in ts: print(t['id'], t['provider_name'], 'tools:', t['tools_count'])
"

curl -s http://localhost:8005/api/agent-templates/generic_agent/validate
```
