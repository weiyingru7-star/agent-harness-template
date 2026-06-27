# Quick Start

Run the Agent Harness Template in 10 minutes.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- Make

## 1. Install Dependencies

```bash
git clone <repo-url> agent-harness-template
cd agent-harness-template

# All dependencies (backend + frontend)
make install
```

## 2. Run Tests

```bash
# Backend tests
make test-api
```

Expected: all tests pass.

## 3. Run Evals

```bash
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py
```

Expected: all eval cases pass.

## 4. Try a Scaffold (dry-run)

```bash
python3 scripts/scaffold_module.py --name demo_module --dry-run
python3 scripts/scaffold_agent.py --name demo_agent --dry-run
python3 scripts/scaffold_eval.py --name demo_eval --dry-run
python3 scripts/scaffold_docs.py --name demo_docs --kind generic --dry-run
```

Expected: no files written, only preview output.

## 5. Start the API (optional)

```bash
make up
make dev-api
curl http://localhost:8005/health
```

Expected:
```json
{"status": "ok", "service": "agent-harness-api"}
```

## 6. Next Steps

- [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md) — how to build your own project from this template
- [README.md](README.md) — full capability reference
- [docs/cli-scaffold-guide.md](docs/cli-scaffold-guide.md) — scaffold commands reference
- [docs/cli-scaffold-troubleshooting.md](docs/cli-scaffold-troubleshooting.md) — common errors
