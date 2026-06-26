# Provider Streaming 流式输出

V0.5.2 为 Provider Runtime 增加最小 streaming contract。

## ProviderStreamEvent

```python
class ProviderStreamEvent(BaseModel):
    event_type: str   # "stream_start" | "stream_delta" | "stream_end" | "stream_error"
    delta: str | None = None
    index: int = 0
    provider: str = ""
    model: str = ""
    metadata: dict = {}
```

## 事件生命周期

```
stream_start   (index=0)
stream_delta   (index=1, delta="Mock ")
stream_delta   (index=2, delta="LLM ")
...
stream_end     (index=N)
```

失败时：

```
stream_start   (index=0)
stream_error   (index=1, delta="error message")
```

## API: POST /api/llm/stream

使用 SSE（Server-Sent Events）格式输出，`content-type: text/event-stream`。

### 请求

```json
{"prompt": "hello", "provider": "mock"}
```

### 响应

```
data: {"event_type":"stream_start","delta":null,"index":0,"provider":"mock","model":"mock","metadata":{}}

data: {"event_type":"stream_delta","delta":"Mock ","index":1,"provider":"mock","model":"mock","metadata":{}}

data: {"event_type":"stream_delta","delta":"LLM ","index":2, ...}

data: {"event_type":"stream_end","delta":null,"index":6,...}
```

## Mock streaming

`MockLLMProvider.stream_text(prompt)` 把完整输出按空格拆分为单词级 delta。
不调用外部 API，结果稳定可复现。

## 与 POST /api/llm/smoke 的关系

| 特性 | /smoke | /stream |
|---|---|---|
| 返回格式 | JSON | SSE text/event-stream |
| 响应模型 | LLMResponse | ProviderStreamEvent 序列 |
| structured | 支持 | 不支持 |
| provider | 可选 | 可选，默认 mock |
| 路径 | 不变 | 新增 |

## 验收

```bash
curl -s -N -X POST http://localhost:8005/api/llm/stream \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello","provider":"mock"}'

# 预期：SSE 格式流式输出
```
