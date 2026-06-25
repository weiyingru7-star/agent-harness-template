# Trace Runtime

V0.2.1 增强 Agent Runtime 的可观察性，让每次 Run 可以形成清晰的
trace、span 和 typed event。

本阶段不实现 checkpoint、resume、retry、human-in-the-loop，也不接外部
tracing 平台。

## 核心概念

### Trace

Trace 表示一次 Run 的完整可观察轨迹。

核心字段：

- `trace_id`：trace 标识。
- `run_id`：关联 Run。
- `spans`：Run 内部执行单元。
- `events`：按 sequence 排序的 typed event。

### Span

Span 表示 Run 中一个可观察执行单元。V0.2.1 中，每个 demo_agent node
对应一个 span-like step。

核心字段：

- `span_id`
- `trace_id`
- `parent_span_id`
- `name`
- `type`
- `status`
- `started_at`
- `ended_at`
- `duration_ms`
- `error`
- `metadata`

### Typed Event

Typed event 是兼容旧事件接口的结构化事件。

旧字段继续保留：

- `type`
- `message`
- `created_at`

新增字段：

- `event_type`
- `trace_id`
- `span_id`
- `parent_span_id`
- `sequence`
- `status`
- `started_at`
- `ended_at`
- `duration_ms`
- `error`
- `metadata`

`type` 和 `event_type` 在 V0.2.1 中保持同步。

## API

旧事件接口保持兼容：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/events
```

新增 trace 接口：

```bash
curl http://localhost:8005/api/runs/$RUN_ID/trace
```

返回结构：

```json
{
  "run_id": "run_xxx",
  "trace_id": "trace_xxx",
  "spans": [
    {
      "id": "span_xxx",
      "trace_id": "trace_xxx",
      "run_id": "run_xxx",
      "step_id": "step_xxx",
      "parent_span_id": null,
      "name": "input_node",
      "type": "node",
      "status": "completed",
      "started_at": "2026-01-01T00:00:00Z",
      "ended_at": "2026-01-01T00:00:00Z",
      "duration_ms": 1,
      "error": null,
      "metadata": {}
    }
  ],
  "events": []
}
```

## 数据库说明

V0.2.1 给开发期表增加了 trace / span / typed event 字段：

- `runs.trace_id`
- `steps.type`
- `steps.trace_id`
- `steps.span_id`
- `steps.parent_span_id`
- `steps.started_at`
- `steps.ended_at`
- `steps.duration_ms`
- `steps.error`
- `steps.metadata`
- `run_events.event_type`
- `run_events.trace_id`
- `run_events.span_id`
- `run_events.parent_span_id`
- `run_events.sequence`
- `run_events.status`
- `run_events.started_at`
- `run_events.ended_at`
- `run_events.duration_ms`
- `run_events.error`
- `run_events.metadata`

当前项目尚未引入迁移工具，开发期仍使用 SQLAlchemy `create_all`。这意味着：

- 新测试库或新开发库会自动创建这些字段。
- 已存在的本地 PostgreSQL 表不会被 `create_all` 自动修改。
- 如旧开发库报字段不存在，请先备份需要的数据，再手动补字段或重建本地开发数据库。

本阶段不会自动删除任何本地数据。

## 当前不实现

- Checkpoint。
- Resume。
- Retry。
- Human-in-the-loop。
- 外部 tracing 平台。
- 多 Agent handoff。
