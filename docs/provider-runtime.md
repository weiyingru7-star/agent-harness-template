# Provider Runtime 模型调用层

V0.5.0 系统化整理 LLM Provider 层，建立 ProviderRequest / ProviderResponse / ProviderError / fallback 的最小合同。不改业务逻辑，只强化模型调用层的结构、错误记录和测试。

## 设计目标

- 统一 ProviderRequest / ProviderResponse / ProviderError 结构化合同。
- `call_provider()` 封装现有 ProviderRouter + provider.generate()，返回 ProviderResponse。
- `call_provider_with_fallback()` 提供主 provider 失败时的 fallback 策略。
- 不改已有 `LLMResponse` 核心字段（`provider`、`output`、`structured_output`）。
- `POST /api/llm/smoke` 响应扩展为包含 `model` / `latency_ms` / `usage` / `finish_reason` / `metadata`。

## ProviderRequest

```python
class ProviderRequest(BaseModel):
    input: str                       # 提示词
    model: str = "mock"              # 模型名称
    messages: list[dict] | None      # 可选 messages 格式
    temperature: float | None        # 可选 temperature
    max_tokens: int | None           # 可选最大 token
    metadata: dict                   # 调用元信息
    timeout_ms: int | None           # 可选超时（V0.5.0 不实现）
```

## ProviderResponse

```python
class ProviderResponse(BaseModel):
    output: str                      # 模型输出
    model: str                       # 实际模型名
    provider: str                    # provider 名称
    latency_ms: int | None           # 调用耗时
    usage: dict                      # token 使用情况
    finish_reason: str | None        # 结束原因
    metadata: dict                   # 扩展元信息
```

## ProviderError

```python
class ProviderError(BaseModel):
    error_type: str                  # 错误类型
    error_message: str               # 错误描述
    provider: str                    # 发生错误的 provider
    model: str = "unknown"            # 模型名
    retryable: bool = False          # 是否可重试
    metadata: dict                   # 扩展信息
```

## call_provider

```python
def call_provider(prompt, provider_name="mock", settings=None) -> ProviderResponse
```

包装 `ProviderRouter.resolve()` + `provider.generate()`，计时并返回结构化 ProviderResponse。

## call_provider_with_fallback

```python
def call_provider_with_fallback(prompt, primary="mock", fallback="mock", settings=None) -> ProviderResponse
```

主 provider 失败时自动 fallback 到备用 provider。metadata 记录 `fallback_from`、`fallback_to`、`fallback_reason`。

## 与现有 Provider 的关系

| 组件 | 是否修改 |
|---|---|
| `MockLLMProvider` | 不改 |
| `OpenAICompatibleProvider` | 不改 |
| `ProviderRouter` | 不改 |
| `LLMResponse` | 新增可选字段（model / latency_ms / usage / finish_reason / metadata） |
| `POST /api/llm/smoke` | 响应扩展，路径和请求不变 |
| `test_llm.py` | 更新断言适配新字段 |

## 验收

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```

### /api/llm/smoke 响应示例

```json
{
  "provider": "mock",
  "output": "Mock LLM response for: hello",
  "structured_output": null,
  "model": "mock",
  "latency_ms": 0,
  "usage": {"prompt_tokens": 1, "completion_tokens": 6, "total_tokens": 7},
  "finish_reason": "stop",
  "metadata": {
    "provider_runtime_version": "v0.5.1",
    "contract": "ProviderResponse",
    "mock": true
  }
}
```
