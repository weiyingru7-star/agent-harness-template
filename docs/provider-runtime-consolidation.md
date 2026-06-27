# Provider Runtime Consolidation Provider 运行时收口

V0.7.7 梳理了项目中两套 provider 抽象的边界。本文档说明 Provider Runtime 的
当前架构分层和新代码开发指引。

## Motivation 动机

项目中存在两套 provider 抽象模块：

- **`app/ai_runtime/`** — 早期构建的基础层，包含 provider 类型定义、具体 provider
  实现和 router。
- **`app/provider_runtime/`** — 后期构建的规范层，包含结构化调用合同和
  timeout/retry/fallback 编排。

两套模块并存会造成概念混淆：`ProviderResult` / `ProviderResponse` 命名相似但含义不
同；mock provider 和 openai-compatible provider 的实现在 `ai_runtime`，而 timeout
/retry/fallback 编排在 `provider_runtime`。新人容易不知道该依赖哪一套。

## Layer Architecture 分层架构

```
┌──────────────────────────────────────────────┐
│            HTTP API Layer (routes/)            │
│  POST /api/llm/smoke → LLMResponse            │
│  POST /api/llm/stream → SSE                   │
│  GET  /api/llm/config  → ProviderConfig       │
└──────────┬───────────────────────────────────┘
           │ imports both
           ▼
┌──────────────────────────────────────────────┐
│    provider_runtime (canonical layer)          │  ← 新功能入口
│                                                │
│  contracts.py:                                 │
│    ProviderRequest / ProviderResponse          │
│    ProviderError / ProviderConfig              │
│                                                │
│  router.py:                                    │
│    call_provider()                             │
│    call_provider_with_timeout_retry()          │
│    call_provider_with_fallback()               │
└──────────┬───────────────────────────────────┘
           │ imports ProviderRouter + errors
           ▼
┌──────────────────────────────────────────────┐
│    ai_runtime (legacy base layer)              │  ← 兼容保留
│                                                │
│  providers.py:                                 │
│    LLMProvider protocol                        │
│    ProviderResult dataclass                    │
│    MockLLMProvider                             │
│    MockFailingLLMProvider                      │
│    MockSlowLLMProvider                         │
│    MockFlakyLLMProvider                        │
│    OpenAICompatibleProvider                    │
│                                                │
│  router.py:                                    │
│    ProviderRouter                              │
│                                                │
│  client.py:                                    │
│    LLMClient / LLMResponse /                   │
│    ProviderStreamEvent                         │
│                                                │
│  structured_output.py:                         │
│    parse_structured_output                     │
└──────────────────────────────────────────────┘
```

## Canonical vs Legacy 规范层 vs 兼容层

| 维度 | `provider_runtime` | `ai_runtime` |
|---|---|---|
| 定位 | **Canonical layer** 规范层 | **Legacy layer** 兼容层 |
| 新功能开发 | ✅ **优先入口** | ❌ 不要新增依赖 |
| 删除计划 | — | 暂不删除（兼容旧 API / tests） |
| 数据合同 | `ProviderRequest` / `ProviderResponse` / `ProviderError`（Pydantic） | `ProviderResult`（dataclass）|
| 调用编排 | `call_provider` / timeout / retry / fallback | `LLMClient.generate()` |
| 具体 provider | 不直接持有 | 持有全部（Mock / Failing / Slow / Flaky / OpenAI） |
| Streaming | 无 streaming 路径 | `LLMClient.generate_stream()` / SSE |
| HTTP response model | 使用 `LLMResponse`（来自 `ai_runtime`） | 定义 `LLMResponse` |

## ProviderResult vs ProviderResponse 关系

| | `ProviderResult` (ai_runtime) | `ProviderResponse` (provider_runtime) |
|---|---|---|
| 定义位置 | `ai_runtime/providers.py` | `provider_runtime/contracts.py` |
| 类型 | `dataclass` | `BaseModel`（Pydantic） |
| 字段 | `output: str`, `metadata: dict \| None` | `output`, `model`, `provider`, `latency_ms`, `usage`, `finish_reason`, `metadata` |
| 用途 | **Provider 内部返回值** | **标准化 API 层响应结构** |
| 转换 | `provider_runtime/router.py` 将 `ProviderResult` 包装为 `ProviderResponse` |

**关键理解**：`LLMResponse`（`ai_runtime/client.py` 中的 Pydantic model）是
`POST /api/llm/smoke` 的 `response_model`。虽然它在 `ai_runtime` 中定义，但它实际
上承载了 `provider_runtime` 合同中的响应字段。这就是混合使用的原因：
`provider_runtime` 的 `call_provider_with_timeout_retry` 返回 `ProviderResponse`，
然后 route 将其字段映射到 `LLMResponse`。

## Provider 实现归属

| Provider | 所在模块 | 归类 |
|---|---|---|
| `MockLLMProvider` | `ai_runtime/providers.py` | 基础 mock provider |
| `MockFailingLLMProvider` | `ai_runtime/providers.py` | 错误模拟 |
| `MockSlowLLMProvider` | `ai_runtime/providers.py` | 超时模拟 |
| `MockFlakyLLMProvider` | `ai_runtime/providers.py` | 重试模拟 |
| `OpenAICompatibleProvider` | `ai_runtime/providers.py` | 真实模型适配 |
| `ProviderRouter` | `ai_runtime/router.py` | provider 实例化工厂 |

所有具体 provider 目前都在 `ai_runtime` 中。`provider_runtime` 通过导入
`ProviderRouter` 来间接使用它们。这是合理的中间状态——具体 provider 实现和
provider 选择逻辑是基础能力，而调用编排（timeout/retry/fallback）是规范化能力。

## Migration Roadmap 后续迁移建议

以下路线图只做参考，**不要在 V0.7.7 实现**：

1. **Phase 1**（当前 V0.7.7）：收口文档边界，完成概念澄清
2. **Phase 2**（未来）：将 `OpenAICompatibleProvider` 从 `ai_runtime` 迁移到
   `provider_runtime`，使用 `httpx` 替代 `urllib`
3. **Phase 3**（未来）：将 mock provider 族迁移到 `provider_runtime/providers/`
4. **Phase 4**（未来）：统一 `LLMResponse` 和 `ProviderResponse` 为一个合同
5. **Phase 5**（未来）：在 `provider_runtime` 中实现 streaming 路径，解耦 `ai_runtime` 的
   streaming 依赖
6. **Phase 6**（未来）：删除 `ai_runtime`（所有消费者已迁移后）

## New Code Guidance 新代码开发指引

### ✅ 新 provider 功能应该

- 在 `provider_runtime/` 中添加新模块
- 依赖 `ProviderRequest` / `ProviderResponse` / `ProviderError` 合同
- 使用 `call_provider_with_timeout_retry` / `call_provider_with_fallback` 进行调用编排

### ❌ 新 provider 功能不应该

- 在 `ai_runtime/` 中添加新模块
- 新增对 `LLMClient` / `ProviderResult` / `ProviderRouter` 的直接依赖（除非 route 层必须）
- 修改 `ai_runtime/` 中的现有行为

### ⚠️ 保持兼容

- `ai_runtime` 中的 `LLMResponse` 是 `POST /api/llm/smoke` 的 `response_model`，不能删除
- `ai_runtime` 中的 `ProviderStreamEvent` 是 streaming endpoint 的返回类型，不能删除
- `ai_runtime` 中的 `ProviderRouter` 被 `provider_runtime` 导入，不能删除

## 相关文档

- [Provider Runtime 总入口](provider-runtime.md)
- [Provider Runtime Contracts](provider-runtime-contracts.md)
- [Provider Runtime Architecture](provider-runtime-architecture.md)
- [Provider Errors](provider-errors.md)
- [Provider Timeout / Retry](provider-timeout-retry.md)
- [Provider Config](provider-config.md)
- [OpenAI-Compatible Provider](openai-compatible-provider.md)
