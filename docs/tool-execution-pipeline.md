# Tool Execution Pipeline 工具执行流水线

## Overview 概述

V0.7.6 extracted the tool execution logic from `RunStore._create_run` into a
dedicated `ToolExecutionPipeline` class. This is a **structural refactor** —
no new features, no changed behavior.

### Motivation 动机

`RunStore._create_run` had grown to ~610 lines, with ~370 lines dedicated to
tool call orchestration: permission checks, sandbox checks, args validation,
timeout/retry, event recording, and ToolCall persistence. Extracting this
pipeline makes Room for future Policy / Guardrail additions without bloating
RunStore further, and clarifies the boundary between run lifecycle management
and tool execution.

## Pipeline Architecture

```
RunStore._create_run (step loop)
  │
  ├── For each step: step.started → execute → step.completed + checkpoint
  │
  └── tool_node step:
        └── ToolExecutionPipeline.execute()
              ├── 1. tool.call.started event
              ├── 2. Permission check (ToolPermissionChecker)
              │     └── denied → ToolCall + tool.call.failed → return
              ├── 3. Sandbox check (ToolSandboxChecker)
              │     └── denied → ToolCall + tool.call.failed → return
              ├── 4. Args validation (ToolArgsValidator)
              │     └── invalid → ToolCall + tool.call.failed → return
              └── 5. Tool execution (execute_with_retry / execute_with_timeout)
                    ├── completed → ToolCall + tool.call.completed
                    └── failed → ToolCall + tool.call.failed (incl. retry events)
```

## Files

| File | Purpose |
|---|---|
| `apps/api/app/tool_runtime/__init__.py` | Package init, re-exports `ToolExecutionPipeline` |
| `apps/api/app/tool_runtime/pipeline.py` | `ToolExecutionPipeline` class + `PipelineResult` |

## Responsibilities

### ToolExecutionPipeline

- Orchestrate the full permission → sandbox → args → execution flow
- Create `tool.call.started`, `tool.call.completed`, `tool.call.failed`,
  `tool.call.retry_scheduled` events
- Create and persist `ToolCall` records
- Return `tool_call_id` and `next_sequence` to the caller
- Dispatch between 4 terminal paths:
  - Permission denied
  - Sandbox denied
  - Args validation failure
  - Tool execution result (completed or failed)

### RunStore (remaining)

- Run lifecycle: `run.created`, `run.started`, `run.completed`, `run.failed`,
  `run.retry_started`, `run.retry_completed`
- Step lifecycle: `step.started`, step model management, `step.completed`,
  `step.failed`, checkpoints
- Tool call query methods: `get_tool_calls`, `get_tool_call`
- Trace, timeline, and checkpoint queries

## Invariants 不变量

All of the following are **unchanged** by this refactor:

- `/api/runs` request/response format
- `/api/runs/{id}/tool-calls` response format
- `/api/tool-calls/{id}` response format
- Event types: `tool.call.started`, `tool.call.completed`, `tool.call.failed`,
  `tool.call.retry_scheduled`
- Event metadata dict shapes
- Sequence number ordering
- ToolCall model fields
- Tool runtime contracts (ToolPermissionChecker, ToolSandboxChecker,
  ToolArgsValidator, execute_with_retry, execute_with_timeout)
- All eval cases
- All test assertions

## Code Reference

```python
from app.tool_runtime import ToolExecutionPipeline

pipeline = ToolExecutionPipeline()
result = pipeline.execute(
    node_trace=node_trace,
    run_id=run.id,
    trace_id=trace_id,
    span_id=span_id,
    step_id=step.id,
    sequence=sequence,
    event_repository=event_repository,
    tool_call_repository=tool_call_repository,
)
tool_call_id = result.tool_call_id
sequence = result.next_sequence
```
