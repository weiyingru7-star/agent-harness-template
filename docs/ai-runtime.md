# AI Runtime

本文档说明 V0.1.0 的 AI Runtime 状态，以及 V0.1.1 根级 `ai_runtime/` 目录的用途。

## 当前能力

V0.1.0 已实现：

- Mock LLM provider。
- OpenAI-compatible provider 基础结构。
- 最小 LLM client。
- structured output 最小解析。
- `/api/llm/smoke` 验证接口。

默认主链路使用 mock provider，不依赖真实外部模型。

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
