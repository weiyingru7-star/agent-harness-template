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

## Future Capabilities（V0.5.x）

- **Timeout**：`ProviderRequest.timeout_ms` 字段已预留，尚未在 runtime 中实现
- **Retry**：provider 级别 retry 尚未实现（Tool Runtime 已有工具级 retry）
- **Provider Eval**：结构化 provider 评估
