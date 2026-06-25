# Failure / Retry Runtime

V0.2.3 adds minimal failure recording and manual retry support for Agent
Runtime.

This stage does not implement resume, time travel, human-in-the-loop, task
queues, external tracing, or automatic retry scheduling.

## Failure Fields

Run fields:

- `error_type`
- `error_message`
- `failed_at`
- `metadata`

Step fields:

- `attempt`
- `max_attempts`
- `error_type`
- `error_message`
- `failed_at`

## Events

Failure and retry use the existing typed event contract.

New event types:

- `step.failed`
- `run.failed`
- `run.retry_started`
- `run.retry_completed`

Reserved for later:

- `step.retry_scheduled`
- `step.retried`

## Retry API

Retry a failed run:

```bash
curl -X POST http://localhost:8005/api/runs/$RUN_ID/retry
```

Behavior:

- Retry is manual.
- Retry re-executes the whole run.
- Retry creates a new `run_id` and `trace_id`.
- The original failed run remains unchanged.
- The retry run metadata includes `retry_of_run_id`.
- No checkpoint resume is performed.

## Test Failure Input

For runtime tests, `demo_agent` fails `skill_node` when the input contains:

```text
__fail__
```

This is a generic test hook for failure-path validation only.

## Compatibility

The following APIs remain compatible:

- `POST /api/runs`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/trace`
- `GET /api/runs/{run_id}/checkpoints`
- `GET /api/checkpoints/{checkpoint_id}`
