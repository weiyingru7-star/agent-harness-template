# OpenAI-Compatible Provider

V0.5.6 为 Provider Runtime 增加第一个真实 LLM provider adapter。通过 `AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL` 配置即可接入 DeepSeek、智谱、Qwen、OpenRouter、硅基流动等兼容 OpenAI Chat Completions 格式的模型。

## 配置

通过环境变量配置：

| 变量 | 示例值 | 说明 |
|---|---|---|
| `AI_PROVIDER` | `openai_compatible` | 切换到真实 provider |
| `AI_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `AI_API_KEY` | `sk-...` | API key（不在响应中暴露） |
| `AI_MODEL` | `gpt-4o-mini` | 模型名 |
| `AI_TIMEOUT` | `30` | 超时（秒） |
| `AI_MAX_ATTEMPTS` | `1` | 最大尝试次数 |
| `AI_FALLBACK_PROVIDER` | `mock` | 失败时回退到 mock |

## ProviderResponse 映射

`OpenAICompatibleProvider._request_chat_completion` 从 OpenAI API 响应中提取以下字段：

| ProviderResult.metadata 字段 | 来源 |
|---|---|
| `provider` | 固定 `"openai_compatible"` |
| `model` | API 响应中的 `model` 字段 |
| `finish_reason` | API 响应 `choices[0].finish_reason` |
| `usage` | API 响应中的 `usage` 对象（含 prompt_tokens / completion_tokens / total_tokens） |

`call_provider` 函数通过 `result.metadata` 动态获取这些字段，自动映射到 `ProviderResponse`。

## Secret 安全

- API key 出现在 `Authorization` header 中发送，不在响应中返回
- `GET /api/llm/config` 只返回 `api_key_configured: true/false`
- HTTP 错误响应中会包含 API 返回的错误消息（如 "Incorrect API key provided"），这是 API 响应的一部分，不是 key 原文

## Fallback / Timeout / Retry

- V0.5.3 fallback 完整兼容：provider 调用失败时自动 fallback 到 mock
- V0.5.4 timeout/retry 完整兼容：通过 `timeout_ms` / `max_attempts` 参数控制
- 网络错误转换为 `ProviderRequestError`，HTTP 错误体中的消息被提取为可读错误

## 手动验收

```bash
# 确保 .env 设置
# AI_PROVIDER=openai_compatible
# AI_BASE_URL=https://api.openai.com/v1
# AI_API_KEY=sk-...
# AI_MODEL=gpt-4o-mini

# smoke 测试
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello, who are you?"}'

# config 检查（不暴露 key）
curl -s http://localhost:8005/api/llm/config | python3 -c "
import json,sys;c=json.load(sys.stdin)
print('provider:',c['provider_name'],'key_configured:',c['api_key_configured'],'model:',c['model'])
"

# fallback（缺 key 时自动 fallback 到 mock）
# AI_API_KEY= 时
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello"}' | python3 -c "
import json,sys;r=json.load(sys.stdin)
print('provider:',r['provider'],'fallback:',r['metadata'].get('fallback_used'))
"
```

## Streaming

V0.5.6 未实现真实 provider streaming。`/api/llm/stream` 端点继续使用 mock streaming。
