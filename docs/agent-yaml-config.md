# Agent YAML Config 增强配置

V0.6.1 增强了 agent 配置的字段能力，支持嵌套 provider / tools / rag / workflow / eval 配置。

## AgentConfig

```python
class AgentConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    runtime_version: str = "v0.6.1"
    provider: str | ProviderRef = "mock"
    tools: list[str] | ToolsConfig = []
    rag: RagConfig
    workflow: WorkflowConfig
    eval: EvalConfig
    policies: list[dict] = []     # V0.8.0 optional policy definitions
    guardrails: list[dict] = []   # V0.8.0 optional guardrail definitions
    metadata: dict = {}
```

## V0.8.0 Policies / Guardrails

AgentConfig 新增两个可选字段：

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `policies` | list[dict] | `[]` | Policy 定义列表，详见 [Policy Guardrail Contract](policy-guardrail-contract.md) |
| `guardrails` | list[dict] | `[]` | Guardrail 定义列表，详见 [Policy Guardrail Contract](policy-guardrail-contract.md) |

没有配置时这两个字段为空列表，validate 仍然返回 valid=true。

## 嵌套字段

### ProviderRef

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `provider_name` | str | `"mock"` | provider 名称 |
| `model` | str \| None | None | 模型名称 |
| `config_ref` | str \| None | None | 配置引用名 |

### ToolsConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `allowed_tools` | list[str] | `[]` | 允许的工具列表 |
| `required_tools` | list[str] | `[]` | 必需的工具列表 |

### RagConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `enabled` | bool | `false` | 是否启用 RAG |
| `collection` | str | `"default"` | RAG collection 名称 |
| `retrieval_mode` | str | `"keyword"` | 检索模式 |

### WorkflowConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `entrypoint` | str \| None | None | 执行入口 |
| `nodes` | list[str] | `[]` | 节点列表 |
| `edges` | list[list[str]] | `[]` | 边列表 |

### EvalConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `cases_path` | str \| None | None | eval case 路径 |
| `required_checks` | list[str] | `[]` | 必需检查项 |

## 简写与嵌套兼容

V0.6.1 同时支持 V0.6.0 的简写格式：

```json
{"provider": "mock", "tools": ["mock_echo"]}
```

和 V0.6.1 的嵌套格式：

```json
{
  "provider": {"provider_name": "openai_compatible", "model": "gpt-4o"},
  "tools": {"allowed_tools": ["mock_echo"], "required_tools": ["mock_echo"]}
}
```

## API

| 方法 | 路径 | 响应 | 用途 |
|---|---|---|---|
| GET | `/api/agent-templates` | `list[AgentTemplate]` | 列表视图 |
| GET | `/api/agent-templates/{id}` | `AgentTemplate` | 简化视图 |
| GET | `/api/agent-templates/{id}/config` | `AgentConfig` | 完整嵌套配置 |
| GET | `/api/agent-templates/{id}/validate` | `list[str]` | 校验错误 |
