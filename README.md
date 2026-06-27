# Agent Harness Template

A business-neutral, reusable AI Agent backend template. Demonstrates a
complete agent platform evolution — from a minimal run loop to a
multi-tenant, tenant-isolated system with RAG, tool ownership guard,
idempotency contract, and async job queue.

**Template, not a project.** Use the scaffold CLI to create your own
agent modules, templates, and eval cases. See [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md).

## Quick Links

- [QUICKSTART.md](QUICKSTART.md) — 10-minute setup
- [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md) — fork vs clone guide
- [docs/cli-scaffold-guide.md](docs/cli-scaffold-guide.md) — scaffold command reference
- [docs/template-release-checklist.md](docs/template-release-checklist.md) — release checklist

## What This Project Demonstrates

This template showcases organic, versioned system design across 9 tagged
releases (v1.0.0 → v1.8.0). Each increment adds a well-defined capability
without breaking the previous ones.

| Area | What it shows |
|---|---|
| **Multi-tenant agent runtime** | Conversation/message API with tenant_id scoping |
| **Tenant-isolated RAG** | Document ingestion and retrieval filtered by tenant |
| **Document cleaning pipeline** | Offline parse/clean/chunk for txt/md/pdf/docx/csv/xlsx |
| **Tool ownership guard** | Runtime permission check on tenant/user/resource before execution |
| **Idempotency contract** | Scoped idempotency_key and sequence_index for message/run APIs |
| **Async job queue** | DB-backed queue with retry, cancel, and worker runtime |
| **Conversation API** | Multi-turn messages, user/assistant roles, run binding |
| **Scaffold system** | CLI generators for modules, agent configs, eval cases, docs |
| **Test & hygiene infrastructure** | 599 tests, business-term checker, template health checker |

## Architecture Overview

```
HTTP API Layer (FastAPI, /api/*)
  ├── /runs              → Run lifecycle (create, trace, timeline, checkpoints)
  ├── /conversations     → Multi-turn conversations with messages
  ├── /jobs              → Async job queue (enqueue, list, cancel)
  ├── /knowledge         → RAG document ingestion and retrieval
  ├── /llm               → LLM provider smoke / stream
  ├── /agent-templates   → Agent template registry + validation
  └── /tool-calls        → Tool call records

Service Layer
  ├── RunStore             → Run/step/event persistence
  ├── ToolExecutionPipeline→ Tool execution (args → permission → sandbox → ownership → execute)
  ├── ConversationStore    → Conversation/message CRUD
  ├── KnowledgeStore       → Document/chunk storage + keyword/vector/hybrid retrieval
  ├── JobQueueService      → Async job queue with status lifecycle
  ├── WorkerRuntime        → Job handler dispatch + retry
  ├── IdempotencyGuard     → Scoped idempotency_key deduplication
  └── ToolOwnershipGuard   → Tenant/user/resource ownership validation

Persistence (SQLAlchemy + SQLite default, PostgreSQL optional)
  ├── Runs, Steps, Events, Checkpoints, ToolCalls
  ├── Conversations, Messages
  ├── Documents, Chunks
  ├── Files, Artifacts
  └── Jobs (V1.8)

Scaffold / CLI
  ├── scripts/scaffold_module.py     → Module skeleton
  ├── scripts/scaffold_agent.py      → Agent template
  ├── scripts/scaffold_eval.py       → Eval case
  ├── scripts/scaffold_docs.py       → Documentation stub
  ├── scripts/clean_documents.py     → Offline document ingestion
  ├── scripts/ingest_cleaned_docs.py → Ingest into RAG store
  └── scripts/run_worker_once.py     → Single-job async worker

Eval / QA
  ├── scripts/run_evals.py           → Trajectory eval (8 cases)
  ├── scripts/run_rag_evals.py       → RAG eval (2 cases)
  ├── scripts/run_workflow_evals.py  → Workflow validation eval (1 case)
  ├── scripts/run_policy_evals.py    → Policy contract eval (22 cases)
  ├── scripts/check_business_terms.py→ Business term contamination checker
  └── scripts/check_template_health.py→ Template integrity checker
```

## Versioned Evolution: V1.0 → V1.8

| Version | Capability |
|---|---|
| **V1.0** | Template foundation — QUICKSTART, TEMPLATE_USAGE, health checks, release checklist |
| **V1.1** | Multi-user contracts — UserContext, Conversation, Message, RunBinding |
| **V1.2** | Message / Conversation API — 6 endpoints, conversation-triggered run |
| **V1.3** | Tenant isolation — required tenant_id, missing→400, mismatch→404 |
| **V1.4** | RAG tenant filter — tenant-scoped ingestion and retrieval |
| **V1.5** | Document cleaning pipeline — 6 file types, Plan A ingestion |
| **V1.6** | Tool permission / ownership guard — tenant/user/resource validation |
| **V1.7** | Concurrency / idempotency contract — scoped idempotency_key, sequence_index |
| **V1.8** | Async job queue / worker runtime — DB-backed queue, retry, cancel, CLI worker |

## Core Capabilities

### Agent Runtime
- Run lifecycle with steps, events, and status tracking
- Trace spans and timeline views
- Checkpoints at each step
- Failure/retry support
- Eval trajectory runner (8 evaluation cases)

### Tool Runtime
Tool execution pipeline with layered validation:
1. Permission level check (safe / restricted / blocked)
2. Sandbox execution mode check
3. Arguments schema validation
4. Timeout control (daemon thread)
5. Retry with configurable max_attempts
6. **Ownership guard** — tenant/user/resource match (V1.6)

### RAG & Ingestion
- Document creation (file upload or direct text)
- Paragraph-based chunking with configurable size and overlap
- Keyword / vector / hybrid retrieval
- **Tenant-scoped retrieval** — chunks filtered by tenant_id (V1.4)
- Embedding provider abstraction (mock default)
- In-memory vector store
- **Offline ingestion pipeline** — parse/clean/chunk 6 file types (V1.5)

### Multi-User & Tenant
- Conversation and message CRUD
- **Tenant_id required** on all conversation operations (V1.3)
- Tenant mismatch returns 404 (no existence leakage)
- User_id consistency check on message/run creation
- Optional tenant_id filtering for RAG retrieval

### Async Job Queue (V1.8)
- Job status lifecycle: queued → running → succeeded / failed → retry
- Idempotent enqueue with scoped key
- Worker runtime with handler registry
- CLI: `scripts/run_worker_once.py`
- API: `POST/GET /api/jobs`, cancel endpoint
- Built-in sample handler: `echo`

### Scaffold CLI
- `python3 scripts/scaffold_module.py --name <name>` — module skeleton
- `python3 scripts/scaffold_agent.py --name <name>` — agent template
- `python3 scripts/scaffold_eval.py --name <name>` — eval case
- `python3 scripts/scaffold_docs.py --name <name> --kind <kind>` — docs stub
- All commands support `--dry-run`, `--force`, `--preview`
- Snake-case validation, business term rejection, path traversal protection

## Engineering Quality

| Metric | Value |
|---|---|
| Backend tests | 599 (at V1.8 release) |
| Eval suites | 5 (agent, RAG, workflow, policy, template health) |
| Eval cases | 33 across all suites |
| Semver tags | 9 (v1.0.0 → v1.8.0) |
| Business term checker | Blocks 10+ industry terms from template core |
| Template health checker | Verifies key files, scaffold scripts, .env hygiene |
| Language | Business-neutral (no domain-specific terms in core) |

## MVP Boundaries / Not Production Yet

This template uses deliberately simple infrastructure suitable for
development, demonstration, and single-process deployment.

| Boundary | Current approach | Production alternative |
|---|---|---|
| Database | SQLite via `create_all` — no migration tool | Alembic / Flyway + PostgreSQL |
| Idempotency guard | In-memory dict (lost on restart) | Redis-backed store |
| Job queue | SQLite-backed MVP, single-process claim_next | Redis / RQ / Celery with SKIP LOCKED |
| Exactly-once | Not guaranteed in multi-instance | Durable queue + idempotent consumers |
| Auth / RBAC | Not implemented | OAuth2 / JWT + role-based policies |
| Worker daemon | None — `run_once` CLI only | Supervisor / K8s / systemd worker |
| Vector store | In-memory (lost on restart) | pgvector / Pinecone / Qdrant |
| Embedding provider | Mock only (deterministic, 8-dim) | OpenAI / Cohere / Ollama |
| Provider runtime | Mock + OpenAI-compatible stub | Real API with rate limiting |
| Observability | Events + timeline (no external export) | OpenTelemetry / Datadog |

## Portfolio Talking Points

If you're using this project in an interview or portfolio, these are
the strongest arguments:

1. **Versioned evolution, not a single commit.** 9 semver tags from
   "minimal template" to "async job queue with tenant isolation."
   Each increment is independently reviewable.

2. **Test and quality infrastructure built in.** 599 tests, 5 eval suites,
   business term checker, template health checker, code hygiene scripts.

3. **Deliberate trade-off documentation.** The MVP Boundaries section
   explicitly calls out what's not production-ready and what would be
   needed. This demonstrates system design judgment.

4. **Business-neutral by construction.** The template core is checked
   for domain-specific language. This makes it a genuine template,
   not a half-finished business project.

5. **Scaffold-first developer experience.** Four CLI commands generate
   complete, business-neutral skeletons. The template is designed to
   be *used*, not just *read*.

## Quick Start

```bash
git clone <repo-url> agent-harness-template
cd agent-harness-template
make install          # backend + frontend dependencies
make test-api         # run all backend tests
```

10-minute setup: see [QUICKSTART.md](QUICKSTART.md).

## How to Run

```bash
# Start infrastructure (PostgreSQL + Redis)
make up

# Start backend API
make dev-api

# Start frontend (optional)
make dev-web

# Health check
curl http://localhost:8005/health
```

## How to Test

```bash
# Backend tests (599 at V1.8 release)
make test-api

# Eval suites
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
python3 scripts/run_workflow_evals.py
python3 scripts/run_policy_evals.py

# Template health
python3 scripts/check_business_terms.py
python3 scripts/check_template_health.py
```

## CLI Scaffold Reference

```bash
python3 scripts/scaffold_module.py --name <module_name>   # new module skeleton
python3 scripts/scaffold_agent.py --name <agent_name>     # new agent template
python3 scripts/scaffold_eval.py --name <eval_name>       # new eval case
python3 scripts/scaffold_docs.py --name <name> --kind <k> # new docs stub
```

All commands support `--dry-run`, `--preview`, and `--force`.
See [docs/cli-scaffold-guide.md](docs/cli-scaffold-guide.md).

## Requirements & Setup

- Python 3.11+
- Node.js 20+
- Docker
- Make

```bash
cp .env.example .env
make install
```

## Historical Notes

The V0.x series (V0.2.0 through V0.9.6) built the internal runtime
foundation: Agent Runtime, Tool Runtime, RAG baseline, Provider
Runtime, Workflow Contracts, Policy/Guardrail contracts, and
Scaffold CLI. These are fully described in git history and in the
project's `docs/` directory. The current portfolio view focuses on
the stable V1.0–V1.8 evolution.

## Future Work

- **V2.0** — Document versioning / knowledge base update
- **V2.1** — Role-based document access policy
- **Production hardening** — Redis-backed idempotency, PostgreSQL
  migration (Alembic), durable job queue, multi-worker support
