# AI Runtime

本文档说明 AI Runtime 的当前状态、Provider 框架和根级 `ai_runtime/` 目录的用途。

## 当前能力

当前已实现：

- Mock LLM provider。
- OpenAI-compatible provider 基础结构。
- Provider Router。
- 最小 LLM client。
- structured output 最小解析。
- `/api/llm/smoke` 验证接口。

默认主链路使用 mock provider，不依赖真实外部模型。

## Provider 接口

LLM provider 使用统一的最小接口：

```text
generate_text(prompt)
generate_json(prompt)
smoke_test()
```

- `generate_text`：返回普通文本。
- `generate_json`：请求 provider 返回 JSON object 字符串，并由 client 做最小解析。
- `smoke_test`：用于验证 provider 是否可用。

V0.1.6 保留旧的 `generate(prompt, structured)` 兼容入口，方便现有代码平滑过渡。

## Provider Router

Provider Router 根据以下优先级选择 provider：

1. 请求中的 `provider`。
2. 环境变量 `AI_PROVIDER`。
3. 默认 `mock`。

当前支持：

- `mock`：默认 provider，测试和本地主链路都可用。
- `openai_compatible`：OpenAI-compatible chat completions adapter。

如果 `openai_compatible` 缺少 `AI_BASE_URL`、`AI_API_KEY` 或 `AI_MODEL`，接口会返回清楚错误，不会影响 mock provider。

## 环境变量

```env
AI_PROVIDER=mock
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_TIMEOUT=30
```

兼容旧配置：

```env
OPENAI_COMPATIBLE_BASE_URL=
OPENAI_COMPATIBLE_API_KEY=
OPENAI_COMPATIBLE_MODEL=gpt-4o-mini
```

新配置优先使用 `AI_*`。旧配置仅作为过渡兼容。

## Smoke Test

Mock provider：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}'
```

Structured mock：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock","structured":true}'
```

OpenAI-compatible provider 未配置时：

```bash
curl -X POST http://localhost:8005/api/llm/smoke \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"openai_compatible"}'
```

预期返回 400，并说明缺少配置。

## 目录关系

当前可运行代码位于：

```text
apps/api/app/ai_runtime/
```

V0.1.1 新增根级目录：

```text
ai_runtime/
```

该目录用于承载未来跨应用共享 AI Runtime 蓝图，不移动现有代码。

## 子目录边界

- `ai_runtime/embeddings/`：embedding provider 预留，不实现 embedding。
- `ai_runtime/vision/`：视觉模型预留，不实现视觉处理。
- `ai_runtime/audio/`：音频模型预留，不实现音频处理。
- `ai_runtime/routing/`：模型路由预留，不实现复杂调度。

## 当前不实现

- 真实外部模型主链路依赖。
- embedding。
- 向量数据库。
- rerank。
- 多模态模型调用。
- 成本路由或生产级 fallback。
