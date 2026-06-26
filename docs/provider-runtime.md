# Provider Runtime 模型调用层

V0.5.0–V0.5.6 构建了一个完整的 Provider Runtime 栈。本文档是整个 Provider Runtime 文档体系的总入口。

## 模块总览

| 模块 | 版本 | 说明 | 文档 |
|---|---|---|---|
| 基础合同 | V0.5.0 | ProviderRequest / ProviderResponse / ProviderError | [Contracts](provider-runtime-contracts.md) |
| 响应合同对齐 | V0.5.1 | smoke 返回对齐 ProviderResponse | [Provider Runtime](provider-runtime.md) |
| 流式输出 | V0.5.2 | ProviderStreamEvent + SSE /api/llm/stream | [Provider Streaming](provider-streaming.md) |
| 错误与回退 | V0.5.3 | MockFailingLLMProvider + fallback | [Provider Errors](provider-errors.md) |
| 超时与重试 | V0.5.4 | MockSlow / MockFlaky + timeout / retry | [Provider Timeout Retry](provider-timeout-retry.md) |
| 配置管理 | V0.5.5 | ProviderConfig + GET /api/llm/config | [Provider Config](provider-config.md) |
| 真实模型适配 | V0.5.6 | OpenAI-compatible adapter | [OpenAI Provider](openai-compatible-provider.md) |

## 架构

详见 [Provider Runtime Architecture](provider-runtime-architecture.md)。

## Provider 能力矩阵

| provider | id | generate | stream_text | 行为 |
|---|---|---|---|---|
| Mock | `mock` | ✅ | ✅ | 返回固定格式 mock 响应 |
| Mock Failing | `mock_failing` | ✅（抛异常） | ✅（抛异常） | 所有调用抛 ProviderRequestError |
| Mock Slow | `mock_slow` | ✅（延迟 3s） | ✅（延迟 3s） | 先 sleep 再返回，配合 timeout 测试 |
| Mock Flaky | `mock_flaky` | ✅（首次失败） | — | 首次抛异常，第二次返回正常 |
| OpenAI-Compatible | `openai_compatible` | ✅ | V0.5.6 未实现 | 通过 env 配置真实 API |

## Provider Selection 规则

```
request.provider 是否显式传值？
  ├─ 是 → 使用 request.provider
  └─ 否 → settings.ai_provider 是否有值？
       ├─ 是 → 使用 settings.ai_provider
       └─ 否 → fallback 到 "mock"
```

## 验收

```bash
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```

## 文档体系

| 文档 | 说明 |
|---|---|
| [Provider Runtime Architecture](provider-runtime-architecture.md) | 架构图与调用链 |
| [Provider Runtime Contracts](provider-runtime-contracts.md) | ProviderRequest / Response / Error / ProviderStreamEvent / ProviderConfig |
| [Provider Config](provider-config.md) | 环境变量、secret 安全、config endpoint |
| [Provider Errors](provider-errors.md) | ProviderError / Fallback |
| [Provider Timeout / Retry](provider-timeout-retry.md) | MockSlow / MockFlaky / timeout / retry |
| [Provider Streaming](provider-streaming.md) | SSE streaming contract |
| [OpenAI-Compatible Provider](openai-compatible-provider.md) | 真实模型集成 |

## 真实 LLM 手动验收

```bash
# 配置（通过 .env）
# AI_PROVIDER=openai_compatible
# AI_BASE_URL=https://api.deepseek.com/v1
# AI_API_KEY=<your-key>
# AI_MODEL=deepseek-chat

make dev-api

# 检查配置（不暴露 key）
curl -s http://localhost:8005/api/llm/config | python3 -m json.tool

# 不传 provider → 使用 AI_PROVIDER
curl -s -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Say hello in one short sentence."}'
```
