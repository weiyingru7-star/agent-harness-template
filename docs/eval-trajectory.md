# Eval Trajectory

V0.2.5 adds a minimal eval runner for the generic Agent Harness runtime. It
executes fixed eval cases against `demo_agent` and checks the run trajectory
produced by the existing APIs.

## Scope

The runner checks:

- run status
- final output text
- event types
- step names
- trace span count
- checkpoint count
- timeline item count

It does not use a real model, external judge, score model, remote eval platform,
permission system, or complex quality gate.

## Case Files

Eval cases live in:

```text
evals/cases/
```

Each case follows `schemas/eval-case.schema.json` and includes:

- `id`
- `name`
- `module_id`
- `input`
- `expected_status`
- `expected_output_contains`
- `expected_events`
- `expected_steps`
- `expected_checkpoints_min`
- `expected_trace_spans_min`
- `expected_timeline_items_min`
- `metadata`

## Runner

Run all evals:

```bash
python3 scripts/run_evals.py
```

Run selected eval files:

```bash
python3 scripts/run_evals.py evals/cases/demo_agent_success.json
```

The runner uses FastAPI `TestClient` and a temporary SQLite database. It does
not require the local API server to be running and does not write to the
development PostgreSQL database.

## Failure Output

When a case fails, the runner prints the case id and the failed expectation, for
example:

```text
FAIL demo_agent_success
  - events missing: run.completed
Summary: 1 passed, 1 failed, 2 total
```

## Current Cases

- `demo_agent_success.json`: checks a completed trajectory.
- `demo_agent_failure.json`: checks a failed trajectory triggered by the generic
  demo failure marker.
