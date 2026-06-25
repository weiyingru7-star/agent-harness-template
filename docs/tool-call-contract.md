# Tool Call Contract

V0.3.0 adds a minimal structured tool call record for Agent Harness. The goal is
to make each tool invocation traceable without adding real external tools,
permissions, sandboxing, timeout handling, or tool retry.

## Data Model

Each tool call includes:

- `id`
- `run_id`
- `step_id`
- `trace_id`
- `span_id`
- `tool_id`
- `tool_name`
- `arguments`
- `result`
- `status`
- `started_at`
- `ended_at`
- `duration_ms`
- `error_type`
- `error_message`
- `metadata`
- `created_at`

The schema contract lives in:

```text
schemas/tool-call.schema.json
```

## Runtime Behavior

The generic `demo_agent` records one tool call during `tool_node` when it invokes
the mock echo tool. The record is linked to the run, step, trace, and span.

Typed events are emitted:

- `tool.call.started`
- `tool.call.completed`

`tool.call.failed` is reserved in the contract for later failure paths, but V0.3.0
does not add tool timeout or tool retry.

## APIs

List tool calls for a run:

```bash
curl http://localhost:8005/api/runs/$RUN_ID/tool-calls
```

Read one tool call:

```bash
curl http://localhost:8005/api/tool-calls/$TOOL_CALL_ID
```

## Timeline And Eval

Timeline items for `tool_node` include `tool_call_id`. Eval cases can use
`expected_tool_calls_min` to guard against losing tool call records in later
changes.
