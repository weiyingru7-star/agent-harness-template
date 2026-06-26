# Provider Runtime Architecture 模型调用架构

V0.5.0–V0.5.6 构建了一个完整的 Provider Runtime 栈。本文档用文本架构图说明整体调用链和 provider selection 规则。

## 架构图

```
┌──────────────────────────────────────────────────┐
│                HTTP API Layer                     │
│  GET /api/llm/config         ProviderConfig      │
│  POST /api/llm/smoke        ProviderResponse     │
│  POST /api/llm/stream       ProviderStreamEvent  │
└──────────┬───────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────┐
│         Provider Selection                        │  V0.5.5–0.5.6
│  request.provider → settings.ai_provider → mock  │
└──────────┬───────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────┐
│    call_provider_with_timeout_retry               │  V0.5.4
│  ┌─ attempt 1                                    │
│  ├─ retry on ProviderRequestError                 │
│  └─ attempt N                                    │
│  retry exhausted → fallback to mock (V0.5.3)      │
└──────────┬───────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────┐
│         ProviderRouter.resolve()                  │
│  mock → MockLLMProvider                           │
│  mock_failing → MockFailingLLMProvider            │
│  mock_slow → MockSlowLLMProvider                  │
│  mock_flaky → MockFlakyLLMProvider                │
│  openai_compatible → OpenAICompatibleProvider     │
└──────────┬───────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────┐
│    Provider.generate() → ProviderResult           │
│    → ProviderResponse                             │
│    → ProviderStreamEvent (streaming)              │
└──────────────────────────────────────────────────┘
```

## Provider Selection 规则

```
request.provider 是否显式传值？
  ├─ 是 → 使用 request.provider
  └─ 否 → settings.ai_provider 是否有值？
       ├─ 是 → 使用 settings.ai_provider
       └─ 否 → fallback 到 "mock"
```

## Provider 能力矩阵

| provider | id | generate | stream_text | 行为 |
|---|---|---|---|---|
| Mock | `mock` | ✅ | ✅ | 返回固定格式 mock 响应 |
| Mock Failing | `mock_failing` | ✅（抛异常） | ✅（抛异常） | 所有调用抛 ProviderRequestError |
| Mock Slow | `mock_slow` | ✅（延迟 3s） | ✅（延迟 3s） | 先 sleep 再返回，配合 timeout 测试 |
| Mock Flaky | `mock_flaky` | ✅（首次失败） | — | 首次抛异常，第二次返回正常 |
| OpenAI-Compatible | `openai_compatible` | ✅ | V0.5.6 未实现 | 通过 env 配置真实 API |

## 调用链

```
POST /api/llm/smoke
  → smoke() route
    → primary = request.provider or settings.ai_provider or "mock"
    → call_provider_with_timeout_retry()
      → _run_with_timeout()           daemon thread timeout
      → ProviderRouter.resolve()      provider 实例化
        → provider.generate()         ProviderResult
      → retry loop (max_attempts)
      → ProviderResponse
    → fallback (on _FALLBACK_ERRORS)
      → ProviderRouter.resolve(fallback)
      → LLMClient.generate()
      → LLMResponse + fallback metadata
```

## 关键设计决策

- provider selection 优先级：explicit request → env config → mock
- retry 优先：同一 provider 上重试 → 耗尽后 fallback 到其他 provider
- timeout 使用 daemon thread，不阻塞主线程
- streaming 独立路径，不经过 timeout/retry 封装
- API key 不在 config response 中暴露

## 相关文档

- [Provider Runtime 总入口](provider-runtime.md)
- [Provider Runtime Contracts](provider-runtime-contracts.md)
- [Provider Config](provider-config.md)
- [Provider Errors](provider-errors.md)
- [Provider Timeout / Retry](provider-timeout-retry.md)
- [Provider Streaming](provider-streaming.md)
