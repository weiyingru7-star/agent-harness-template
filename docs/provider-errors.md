# Provider Errors / Fallback 错误与回退

V0.5.3 为 Provider Runtime 增加结构化错误和 fallback 最小路径。

## ProviderError

已在 V0.5.0 定义的 `ProviderError` model：

```python
class ProviderError(BaseModel):
    error_type: str               # 错误类型
    error_message: str            # 错误描述
    provider: str                 # 发生错误的 provider
    model: str = "unknown"        # 模型名称
    retryable: bool = False       # 是否可重试
    metadata: dict = {}
```

## MockFailingLLMProvider

新增 `MockFailingLLMProvider`（`id="mock_failing"`），所有方法都抛 `ProviderRequestError`。
用于测试 provider 失败和 fallback 路径。

通过 `ProviderRouter.resolve("mock_failing")` 获取。

## Fallback 策略

### POST /api/llm/smoke

新增可选字段 `fallback`：

```json
{"prompt": "hello", "provider": "mock_failing", "fallback": "mock"}
```

当 primary provider 失败时，自动 fallback 到指定 provider，响应 metadata 包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `fallback_used` | bool | 是否触发了 fallback |
| `fallback_from` | str | 主 provider 名称 |
| `fallback_to` | str | 备用 provider 名称 |
| `fallback_reason` | str | 失败原因（含异常类型和消息） |
| `primary_error_type` | str | 异常类型名（如 `ProviderRequestError`） |

不传 `fallback` 时行为与 V0.5.2 完全一致（失败返回 400）。

### call_provider_with_fallback

`app/provider_runtime/router.py` 中的 fallback 函数同样支持完整的 fallback metadata。

### Stream

V0.5.3 **不实现** stream endpoint 的 fallback。stream fallback 是 future 能力。

## 验收

```bash
# fallback 正常路径
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_failing","fallback":"mock"}' \
  | python3 -c "import json,sys;r=json.load(sys.stdin);print('provider:',r['provider'],'fallback:',r['metadata'].get('fallback_used'),'error:',r['metadata'].get('primary_error_type'))"

# 无 fallback：mock_failing 返回 400
curl -s -w '\n%{http_code}' -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_failing"}' | tail -1
```
