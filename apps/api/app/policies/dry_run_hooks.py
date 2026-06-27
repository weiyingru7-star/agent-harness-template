"""Guardrail dry-run hooks — input, tool, provider, RAG evaluation helpers.

V0.8.6–V0.8.8 — dry-run only, no enforcement, no runtime changes.
Wraps PolicyDryRunEvaluator with standardised context construction and
event recording patterns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.policies.evaluator import PolicyDryRunEvaluator


def _should_run(policies: list[dict] | None, guardrails: list[dict] | None) -> bool:
    """No-op when no policies/guardrails configured."""
    return bool(policies) or bool(guardrails)


# ── Input guardrail (V0.8.6) ───────────────────────────────────────


def run_input_guardrail(
    *,
    task_input: str,
    run_id: str,
    run_metadata: dict,
    trace_id: str,
    sequence: int,
    event_repository,
    policies: list[dict] | None = None,
    guardrails: list[dict] | None = None,
) -> int:
    """Evaluate input guardrail in dry-run mode.

    Builds an input-scope EvaluationContext from the task input and
    calls PolicyDryRunEvaluator. Records the decision as a
    guardrail.dry_run.completed event.

    No-op when both policies and guardrails are empty/None.
    Never blocks, never raises, never changes run status.

    Returns the next sequence number (unchanged in no-op mode).
    """
    if not _should_run(policies, guardrails):
        return sequence

    try:
        now = datetime.now(timezone.utc)
        context = {
            "context_id": f"input_guardrail_{run_id[:16]}",
            "scope": "input",
            "subject": {
                "type": "run_input",
                "id": run_id,
                "content": task_input,
                "payload": {"char_length": len(task_input)},
            },
            "attributes": {
                "module_id": run_metadata.get("module_id", ""),
            },
            "metadata": {},
        }

        result = PolicyDryRunEvaluator.evaluate(
            policies=policies or [],
            guardrails=guardrails or [],
            context=context,
        )
        event_repository.create(
            run_id=run_id,
            event_type="guardrail.dry_run.completed",
            message="Input guardrail dry-run completed",
            trace_id=trace_id,
            sequence=sequence,
            status="completed",
            started_at=now,
            ended_at=now,
            metadata={
                "scope": "input",
                "execution_mode": "dry_run",
                "final_action": result.get("final_action", "allow"),
                "decision_count": len(result.get("decisions", [])),
            },
        )
        return sequence + 1
    except Exception:
        return sequence


# ── Tool guardrail (V0.8.7) ────────────────────────────────────────


def run_tool_guardrail(
    *,
    tool_name: str,
    tool_arguments: dict,
    run_id: str,
    trace_id: str,
    span_id: str,
    sequence: int,
    event_repository,
    policies: list[dict] | None = None,
    guardrails: list[dict] | None = None,
) -> int:
    """Evaluate tool guardrail in dry-run mode.

    Builds a tool-scope EvaluationContext and calls
    PolicyDryRunEvaluator. Records the decision as a
    guardrail.dry_run.completed event.

    No-op when both policies and guardrails are empty/None.
    Never blocks, never raises, never changes tool execution.
    """
    if not _should_run(policies, guardrails):
        return sequence

    try:
        now = datetime.now(timezone.utc)
        context = {
            "context_id": f"tool_guardrail_{run_id[:16]}",
            "scope": "tool",
            "subject": {
                "type": "tool_call",
                "id": tool_name,
                "content": str(tool_arguments),
                "payload": dict(tool_arguments),
            },
            "attributes": {
                "tool_name": tool_name,
                "arg_keys": list(tool_arguments.keys()),
                "has_args": bool(tool_arguments),
            },
            "metadata": {},
        }

        result = PolicyDryRunEvaluator.evaluate(
            policies=policies or [],
            guardrails=guardrails or [],
            context=context,
        )
        event_repository.create(
            run_id=run_id,
            event_type="guardrail.dry_run.completed",
            message=f"Tool guardrail dry-run completed for {tool_name}",
            trace_id=trace_id,
            span_id=span_id,
            sequence=sequence,
            status="completed",
            started_at=now,
            ended_at=now,
            metadata={
                "scope": "tool",
                "execution_mode": "dry_run",
                "final_action": result.get("final_action", "allow"),
                "decision_count": len(result.get("decisions", [])),
                "tool_name": tool_name,
            },
        )
        return sequence + 1
    except Exception:
        return sequence


# ── Provider guardrail (V0.8.8) ────────────────────────────────────


def run_provider_guardrail(
    *,
    provider_name: str,
    model: str,
    prompt: str,
    policies: list[dict] | None = None,
    guardrails: list[dict] | None = None,
) -> dict:
    """Evaluate provider guardrail in dry-run mode.

    Returns a DecisionResult dict (no event_repository available in
    provider runtime). Caller is responsible for using the result.
    No-op marker via {"_noop": True}.
    """
    if not _should_run(policies, guardrails):
        return {"_noop": True}

    context = {
        "context_id": f"provider_guardrail_{uuid4().hex[:12]}",
        "scope": "provider",
        "subject": {
            "type": "provider_request",
            "id": provider_name,
            "content": prompt,
            "payload": {"char_length": len(prompt)},
        },
        "attributes": {
            "provider_name": provider_name,
            "model": model or "",
        },
        "metadata": {},
    }

    return PolicyDryRunEvaluator.evaluate(
        policies=policies or [],
        guardrails=guardrails or [],
        context=context,
    )


# ── RAG guardrail (V0.8.8) ─────────────────────────────────────────


def run_rag_guardrail(
    *,
    query: str,
    collection: str,
    retrieval_mode: str,
    policies: list[dict] | None = None,
    guardrails: list[dict] | None = None,
) -> dict:
    """Evaluate RAG guardrail in dry-run mode.

    Returns a DecisionResult dict (no event_repository available in
    RAG runtime). Caller is responsible for using the result.
    No-op marker via {"_noop": True}.
    """
    if not _should_run(policies, guardrails):
        return {"_noop": True}

    context = {
        "context_id": f"rag_guardrail_{uuid4().hex[:12]}",
        "scope": "rag",
        "subject": {
            "type": "rag_query",
            "id": collection,
            "content": query,
            "payload": {"query_length": len(query)},
        },
        "attributes": {
            "collection": collection,
            "retrieval_mode": retrieval_mode or "keyword",
        },
        "metadata": {},
    }

    return PolicyDryRunEvaluator.evaluate(
        policies=policies or [],
        guardrails=guardrails or [],
        context=context,
    )
