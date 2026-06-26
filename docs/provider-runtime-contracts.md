# Provider Runtime Contracts 模型调用合同

V0.5.0 定义的结构化 Provider 合同。

## 合同一览

| 合同 | 位置 | 主要字段 |
|---|---|---|
| ProviderRequest | `provider_runtime/contracts.py` | input, model, messages, temperature, max_tokens, metadata, timeout_ms |
| ProviderResponse | `provider_runtime/contracts.py` | output, model, provider, latency_ms, usage, finish_reason, metadata |
| ProviderError | `provider_runtime/contracts.py` | error_type, error_message, provider, model, retryable, metadata |

## Fallback metadata

当 `call_provider_with_fallback` 触发 fallback 时，response.metadata 包含：

| 字段 | 说明 |
|---|---|
| `fallback_from` | 主 provider 名称 |
| `fallback_to` | 备用 provider 名称 |
| `fallback_reason` | 失败原因 |

## LLMResponse（smoke API）

V0.5.1 开始，`POST /api/llm/smoke` 的响应对齐 ProviderResponse contract：

| 字段 | 类型 | 来源 |
|---|---|---|
| `provider` | str | provider.id |
| `output` | str | provider.generate() 结果 |
| `structured_output` | dict \| null | JSON 解析结果 |
| `model` | str | provider.model 或 provider.id |
| `latency_ms` | int | 调用耗时 |
| `usage` | dict | prompt_tokens / completion_tokens / total_tokens（估算） |
| `finish_reason` | str | 固定 "stop" |
| `metadata` | dict | provider_runtime_version / contract / mock 标记 |

## ProviderStreamEvent（streaming）

V0.5.2 新增 SSE streaming contract：

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_type` | str | stream_start / stream_delta / stream_end / stream_error |
| `delta` | str \| null | stream_delta 时返回该片段文本 |
| `index` | int | 从 0 开始连续的事件序号 |
| `provider` | str | provider 名称 |
| `model` | str | 模型名称 |
| `metadata` | dict | 扩展元信息 |

### API: POST /api/llm/stream

SSE 格式，`content-type: text/event-stream`。每个事件一行 `data: <json>\n\n`。

## Future Capabilities（V0.5.x）

- **Timeout**：`ProviderRequest.timeout_ms` 字段已预留，尚未在 runtime 中实现
- **Retry**：provider 级别 retry 尚未实现（Tool Runtime 已有工具级 retry）
- **Provider Eval**：结构化 provider 评估
