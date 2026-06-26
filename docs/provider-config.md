# Provider Config 模型配置管理

V0.5.5 为 Provider Runtime 增加最小配置管理能力。

## ProviderConfig

```python
class ProviderConfig(BaseModel):
    provider_name: str = "mock"         # 当前使用的 provider
    base_url: str | None = None          # base URL（不含 API key）
    api_key_configured: bool = False     # 是否配置了 API key（不暴露 key 原文）
    model: str = ""                      # 模型名称
    timeout_ms: int | None = None        # 超时（毫秒）
    max_attempts: int = 1               # 最大尝试次数
    fallback_provider: str = "mock"      # fallback provider
    streaming_enabled: bool = True       # 是否启用 streaming
    metadata: dict = {}
```

## Env 变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `AI_PROVIDER` | `"mock"` | 默认 provider |
| `AI_BASE_URL` | `""` | OpenAI-compatible base URL |
| `AI_API_KEY` | `""` | API key（不在响应中暴露） |
| `AI_MODEL` | `"gpt-4o-mini"` | 默认模型 |
| `AI_TIMEOUT` | `30` | 超时（秒） |
| `AI_MAX_ATTEMPTS` | `1` | 最大尝试次数 |
| `AI_FALLBACK_PROVIDER` | `"mock"` | fallback provider |
| `AI_STREAMING_ENABLED` | `true` | streaming 开关 |

## Secret 安全

- API key **不会出现在任何 API 响应中**
- `GET /api/llm/config` 只返回 `api_key_configured: true/false`
- `.env.example` 只放空占位符
- 日志中不打印 AI_API_KEY 原文

## GET /api/llm/config

```json
{
  "provider_name": "mock",
  "base_url": null,
  "api_key_configured": false,
  "model": "gpt-4o-mini",
  "timeout_ms": 30000,
  "max_attempts": 1,
  "fallback_provider": "mock",
  "streaming_enabled": true,
  "metadata": {}
}
```

## Smoke metadata

`POST /api/llm/smoke` 的 metadata 新增：

| 字段 | 值 |
|---|---|
| `configured_provider` | 当前 provider 名称 |
| `configured_model` | 配置的模型名 |
| `config_source` | 固定 `"env"` |

## 验收

```bash
curl -s http://localhost:8005/api/llm/config | python3 -m json.tool
```
