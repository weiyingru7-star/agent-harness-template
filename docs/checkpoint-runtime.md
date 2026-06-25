# Checkpoint Runtime

V0.2.2 adds minimal checkpoint snapshots for Agent Runtime observability.

Checkpoint only saves state snapshots after completed steps. It does not
implement resume, retry, time travel, human-in-the-loop, or external tracing.

## Fields

Each checkpoint includes:

- `id`
- `run_id`
- `step_id`
- `trace_id`
- `span_id`
- `checkpoint_index`
- `state`
- `metadata`
- `created_at`

## API

List checkpoints for a run:

```bash
curl http://localhost:8005/api/runs/$RUN_ID/checkpoints
```

Read one checkpoint:

```bash
curl http://localhost:8005/api/checkpoints/$CHECKPOINT_ID
```

## Behavior

- A successful demo run creates four checkpoints.
- The checkpoints correspond to `input_node`, `skill_node`, `tool_node`, and `final_node`.
- `checkpoint_index` starts at 1 and increases within the run.
- `/events` and `/trace` stay compatible and do not include checkpoint data by default.

## Development Database

New test databases create the `checkpoints` table automatically through
SQLAlchemy `create_all`.

Existing local PostgreSQL development databases may need this table added once.
Use `CREATE TABLE IF NOT EXISTS` and do not delete existing data.
