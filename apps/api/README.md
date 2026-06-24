# Agent Harness API

FastAPI backend for the Agent Harness template.

Stage 1 only exposes:

- `GET /health`

Run locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test:

```bash
pytest
```
