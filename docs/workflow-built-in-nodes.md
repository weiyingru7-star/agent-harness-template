# Built-in Workflow Nodes 内置工作流节点

V0.7.2 定义了 6 种业务无关的 built-in workflow node contracts，让节点有明确的 config / inputs / outputs 合同。

## 节点合同一览

| 类型 | 允许的 config key | 预期输入 | 预期输出 |
|---|---|---|---|
| `input` | input_schema, default | — | payload |
| `provider` | provider_name, model, prompt_template, temperature | prompt | output, usage |
| `tool` | tool_name, args_template | input | result, status |
| `rag` | collection, retrieval_mode, query_template, limit | query | results, citations |
| `decision` | routes, default_route | input | selected_route |
| `final` | output_template | input | final_output |

## input node

```json
{"id": "input_node", "type": "input", "config": {}, "inputs": [], "outputs": ["payload"]}
```

只定义输入接口，不处理真实输入。

## provider node

```json
{"id": "provider_node", "type": "provider",
 "config": {"provider_name": "mock", "model": "mock", "temperature": 0.7},
 "inputs": ["prompt"], "outputs": ["output", "usage"]}
```

不调用真实 provider。

## tool node

```json
{"id": "tool_node", "type": "tool",
 "config": {"tool_name": "mock_echo"},
 "inputs": ["input"], "outputs": ["result", "status"]}
```

不执行真实 tool。

## rag node

```json
{"id": "rag_node", "type": "rag",
 "config": {"collection": "default", "retrieval_mode": "keyword", "limit": 5},
 "inputs": ["query"], "outputs": ["results", "citations"]}
```

不执行真实 retrieval。

## decision node

```json
{"id": "dec_node", "type": "decision",
 "config": {"routes": [{"to": "node_a", "route_key": "option_1"}, {"to": "node_b", "route_key": "option_2"}]},
 "inputs": ["input"], "outputs": ["selected_route"]}
```

不执行真实 decision logic。

## final node

```json
{"id": "final_node", "type": "final",
 "config": {"output_template": "{{output}}"},
 "inputs": ["input"], "outputs": ["final_output"]}
```

不生成真实最终回复。

## Validator 校验

`WorkflowValidator.validate_contract(node)` 检查节点的 `outputs` 是否包含了合同要求的预期输出字段。

## 完整示例（generic_agent）

```json
"workflow": {
  "entrypoint": "input_node",
  "nodes": [
    {"id": "input_node", "type": "input", "config": {}, "inputs": [], "outputs": ["payload"]},
    {"id": "provider_node", "type": "provider", "config": {"provider_name": "mock", "model": "mock"}, "inputs": ["prompt"], "outputs": ["output", "usage"]},
    {"id": "tool_node", "type": "tool", "config": {"tool_name": "mock_echo"}, "inputs": ["input"], "outputs": ["result", "status"]},
    {"id": "final_node", "type": "final", "config": {}, "inputs": ["input"], "outputs": ["final_output"]}
  ],
  "edges": [
    {"from": "input_node", "to": "provider_node"},
    {"from": "provider_node", "to": "tool_node"},
    {"from": "tool_node", "to": "final_node"}
  ],
  "terminal_nodes": ["final_node"]
}
```
