# Provider Timeout / Retry 超时与重试

V0.5.4 为 Provider Runtime 增加 provider 调用级 timeout / retry 最小能力。

## ProviderTimeoutError

新增异常类，继承自 `ProviderRequestError`：

```python
class ProviderTimeoutError(ProviderRequestError):
    """Raised when provider call exceeds timeout_ms."""
```

## MockSlowLLMProvider

`id="mock_slow"`，带 `delay_ms` 参数（默认 3000ms）。`generate()` 先 sleep 再返回。
用于测试 provider timeout。使用 `call_provider_with_timeout_retry` 时配合 `timeout_ms` 参数触发超时。

## MockFlakyLLMProvider

`id="mock_flaky"`，内部计数器首次调用抛 `ProviderRequestError`，第二次起正常返回。
用于测试 provider retry。使用 `call_provider_with_timeout_retry` 时配合 `max_attempts=2`。

## call_provider_with_timeout_retry

`app/provider_runtime/router.py` 中新增：

```python
def call_provider_with_timeout_retry(
    prompt: str,
    provider_name: str = "mock",
    max_attempts: int = 1,
    timeout_ms: int | None = None,
    structured: bool = False,
    settings: Settings | None = None,
) -> ProviderResponse:
```

### Timeout 实现

daemon thread + `join(timeout)` 模式。线程在 `timeout_ms` 内未完成时抛出 `ProviderTimeoutError`。

### Retry 实现

简单循环：对 `ProviderRequestError` 和 `ProviderTimeoutError` 重试（retyable 错误）。
`ProviderConfigurationError` 和 `ValueError` 不重试。

### Retry Metadata

当 retry 被触发时，`ProviderResponse.metadata` 包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `attempts` | list | 每次尝试记录 `{attempt_index, status, error_type?, error_message?, latency_ms?}` |
| `max_attempts` | int | 最大尝试次数 |
| `retry_count` | int | 实际重试次数 |
| `retried` | bool | 是否曾重试 |
| `final_attempt_status` | str | 最终尝试状态（`"completed"`） |

### 与 Fallback 的关系

retry 优先（在同一 provider 上重试），retry 耗尽后异常传播到路由层 → fallback 到 mock。

```
primary provider → retry loop → 如果 retry 耗尽 → fallback 到 mock
```

## API: POST /api/llm/smoke

新增可选字段：

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `timeout_ms` | int \| null | null | 超时时间（ms），不传则无超时 |
| `max_attempts` | int | 1 | 最大尝试次数，1=不重试 |

```json
{"prompt": "hello", "provider": "mock_flaky", "max_attempts": 2}
```

## Stream

V0.5.4 不实现 stream timeout/retry。文档中明确说明 future 能力。

## 验收

```bash
# flaky → retry → 成功
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock_flaky","max_attempts":2}'
```
