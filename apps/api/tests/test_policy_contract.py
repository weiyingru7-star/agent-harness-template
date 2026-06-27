"""Tests for V0.8.0 Policy / Guardrail Contract.

Validates structural constraints only — no policy execution.
"""

import pytest

from app.policies import (
    Condition,
    Guardrail,
    Policy,
    PolicyDryRunEvaluator,
    PolicyValidationResult,
    PolicyValidator,
    Rule,
)
from app.policies.models import POLICY_ACTIONS, POLICY_SCOPES
from app.policies.validator import ERROR_CODES


# ── Valid policy structure ──────────────────────────────────────────

def test_policy_valid_structure() -> None:
    policy = Policy(
        id="length_check",
        name="Length Check",
        version="1.0.0",
        scope="input",
        rules=[
            Rule(
                id="max_length",
                condition=Condition(type="expression", expression="len(input) > 1000"),
                action="warn",
                severity="medium",
                message="Input exceeds recommended length",
            ),
        ],
        default_action="allow",
    )
    assert policy.id == "length_check"
    assert policy.scope == "input"
    assert len(policy.rules) == 1
    assert policy.default_action == "allow"
    assert policy.enabled is True


def test_policy_valid_empty_rules() -> None:
    result = PolicyValidator.validate_policies([
        {"id": "empty_policy", "name": "Empty", "version": "1.0.0", "scope": "tool", "rules": []},
    ])
    assert result.valid is True


# ── Invalid scope ────────────────────────────────────────────────────

def test_policy_invalid_scope() -> None:
    result = PolicyValidator.validate_policies([
        {"id": "bad_scope", "name": "Bad", "version": "1.0.0", "scope": "database", "rules": []},
    ])
    assert result.valid is False
    assert any("scope" in e.lower() for e in result.errors)
    assert any(
        item.code == ERROR_CODES["scope_invalid"]
        for item in result.error_items
    )


# ── Invalid action ───────────────────────────────────────────────────

def test_policy_invalid_default_action() -> None:
    result = PolicyValidator.validate_policies([
        {"id": "bad_action", "name": "Bad", "version": "1.0.0", "scope": "input", "default_action": "delete", "rules": []},
    ])
    assert result.valid is False
    assert any("action" in e.lower() for e in result.errors)


def test_policy_invalid_rule_action() -> None:
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "output",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "nuke"},
            ],
        },
    ])
    assert result.valid is False
    assert any("action" in e.lower() for e in result.errors)


# ── Invalid condition type ───────────────────────────────────────────

def test_policy_invalid_condition_type() -> None:
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "regex"}},
            ],
        },
    ])
    assert result.valid is False
    assert any("condition" in e.lower() for e in result.errors)
    assert any(
        item.code == ERROR_CODES["condition_type_invalid"]
        for item in result.error_items
    )


# ── Missing rule fields ──────────────────────────────────────────────

def test_policy_rule_missing_id() -> None:
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "tool",
            "rules": [
                {"condition": {"type": "always"}},
            ],
        },
    ])
    assert result.valid is False
    assert any("rule id" in e.lower() for e in result.errors)


def test_policy_rule_missing_condition() -> None:
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "rag",
            "rules": [
                {"id": "r1"},
            ],
        },
    ])
    assert result.valid is False
    assert any("condition" in e.lower() for e in result.errors)


# ── Invalid severity ─────────────────────────────────────────────────

def test_policy_invalid_severity() -> None:
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "provider",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "severity": "catastrophic"},
            ],
        },
    ])
    assert result.valid is False
    assert any("severity" in e.lower() for e in result.errors)


# ── Guardrail structure ──────────────────────────────────────────────

def test_guardrail_valid_structure() -> None:
    guardrail = Guardrail(
        id="gr_input_length",
        name="Input Length Guardrail",
        type="input",
        policy_ref="length_check",
        action="warn",
    )
    assert guardrail.id == "gr_input_length"
    assert guardrail.type == "input"
    assert guardrail.policy_ref == "length_check"
    assert guardrail.enabled is True


def test_guardrail_invalid_type() -> None:
    result = PolicyValidator.validate_guardrails([
        {"id": "gr1", "name": "GR1", "type": "database"},
    ])
    assert result.valid is False
    assert any("type" in e.lower() for e in result.errors)


def test_guardrail_invalid_action() -> None:
    result = PolicyValidator.validate_guardrails([
        {"id": "gr1", "name": "GR1", "type": "input", "action": "halt"},
    ])
    assert result.valid is False


# ── guardrail policy_ref not found (warning) ─────────────────────────

def test_guardrail_policy_ref_not_found_warns() -> None:
    result = PolicyValidator.validate_guardrails(
        [{"id": "gr1", "name": "GR1", "type": "input", "policy_ref": "nonexistent"}],
        policy_ids={"some_other_policy"},
    )
    assert result.valid is True  # warning only, not an error
    assert len(result.warnings) >= 1
    assert any("policy_ref" in w.lower() for w in result.warnings)


def test_guardrail_policy_ref_found_no_warning() -> None:
    result = PolicyValidator.validate_guardrails(
        [{"id": "gr1", "name": "GR1", "type": "input", "policy_ref": "my_policy"}],
        policy_ids={"my_policy"},
    )
    assert result.valid is True
    assert len(result.warnings) == 0


# ── Guardrail default action ─────────────────────────────────────────

def test_guardrail_default_action_is_allow() -> None:
    guardrail = Guardrail(id="gr1", name="GR1", type="output")
    assert guardrail.action == "allow"


# ── Guardrail type aligns with policy scope enum ─────────────────────

def test_guardrail_types_match_policy_scopes() -> None:
    from app.policies.models import GUARDRAIL_TYPES
    assert GUARDRAIL_TYPES == POLICY_SCOPES


# ── Agent template integration ───────────────────────────────────────

def test_generic_agent_validate_passes_with_empty_policies() -> None:
    from app.registries.agent_template import AgentTemplateRegistry
    loader = AgentTemplateRegistry()
    result = loader.validate_template("generic_agent")
    assert result.valid is True


def test_policy_with_valid_condition_types() -> None:
    for ct in ("always", "expression", "match", "route"):
        result = PolicyValidator.validate_policies([
            {
                "id": f"ct_{ct}", "name": ct, "version": "1.0.0", "scope": "input",
                "rules": [{"id": "r1", "condition": {"type": ct}}],
            },
        ])
        assert result.valid is True, f"condition type '{ct}' should be valid"


# ── Task: no execution ───────────────────────────────────────────────

def test_policy_validator_does_not_execute_conditions() -> None:
    """PolicyValidator only checks structure, never evaluates expressions."""
    result = PolicyValidator.validate_policies([
        {
            "id": "p1", "name": "P1", "version": "1.0.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "expression", "expression": "__NO_EXECUTION__"}},
            ],
        },
    ])
    # Should pass — expression content is not evaluated
    assert result.valid is True


# ── Decision Contract Tests (V0.8.2) ────────────────────────────────

def test_decision_contract_valid() -> None:
    result = PolicyValidator.validate_decision_contract({
        "decision_id": "dec_001",
        "action": "block",
        "severity": "high",
        "reason": "Blocked by policy",
        "matched_rules": ["rule_a"],
    })
    assert result.valid is True


def test_decision_contract_missing_action() -> None:
    result = PolicyValidator.validate_decision_contract({
        "decision_id": "dec_no_action",
    })
    assert result.valid is False
    assert any("action" in e.lower() for e in result.errors)
    assert any(
        item.code == "DECISION_ACTION_MISSING"
        for item in result.error_items
    )


def test_decision_contract_invalid_action() -> None:
    result = PolicyValidator.validate_decision_contract({
        "decision_id": "dec_bad",
        "action": "delete_all",
    })
    assert result.valid is False
    assert any("action" in e.lower() for e in result.errors)


def test_decision_contract_invalid_severity() -> None:
    result = PolicyValidator.validate_decision_contract({
        "decision_id": "dec_sev",
        "action": "warn",
        "severity": "planet_killer",
    })
    assert result.valid is False
    assert any("severity" in e.lower() for e in result.errors)


def test_decision_result_valid() -> None:
    result = PolicyValidator.validate_decision_result({
        "valid": True,
        "final_action": "allow",
        "decisions": [
            {"decision_id": "d1", "action": "allow", "severity": "low"},
            {"decision_id": "d2", "action": "warn", "severity": "medium"},
        ],
    })
    assert result.valid is True


def test_decision_result_invalid_final_action() -> None:
    result = PolicyValidator.validate_decision_result({
        "valid": True,
        "final_action": "explode",
    })
    assert result.valid is False
    assert any("final_action" in e.lower() for e in result.errors)


def test_decision_result_propagates_child_errors() -> None:
    result = PolicyValidator.validate_decision_result({
        "valid": False,
        "final_action": "allow",
        "decisions": [
            {"decision_id": "d1", "action": "allow"},
            {"decision_id": "d2", "action": "invalid_action"},
        ],
    })
    assert result.valid is False
    # Should have error about d2's invalid action
    assert any("decisions" in (item.path or "") for item in result.error_items if item.path)


# ── Evaluation Context Tests (V0.8.3) ───────────────────────────────

def test_evaluation_context_valid() -> None:
    result = PolicyValidator.validate_evaluation_context({
        "context_id": "ctx_001",
        "scope": "input",
        "subject": {"type": "user_message", "content": "hello"},
        "attributes": {"channel": "web"},
    })
    assert result.valid is True


def test_evaluation_context_invalid_scope() -> None:
    result = PolicyValidator.validate_evaluation_context({
        "context_id": "ctx_bad",
        "scope": "storage",
        "subject": {"type": "query"},
    })
    assert result.valid is False
    assert any("scope" in e.lower() for e in result.errors)
    assert any(
        item.code == "CONTEXT_SCOPE_INVALID"
        for item in result.error_items
    )


def test_evaluation_context_missing_subject() -> None:
    result = PolicyValidator.validate_evaluation_context({
        "context_id": "ctx_no_sub",
        "scope": "tool",
    })
    assert result.valid is False
    assert any("subject" in e.lower() for e in result.errors)


def test_evaluation_context_invalid_attributes_type() -> None:
    result = PolicyValidator.validate_evaluation_context({
        "context_id": "ctx_attr",
        "scope": "output",
        "subject": {"type": "response"},
        "attributes": "bad_string",
    })
    assert result.valid is False
    assert any("attributes" in e.lower() for e in result.errors)


def test_evaluation_context_not_an_object() -> None:
    result = PolicyValidator.validate_evaluation_context("not_a_dict")
    assert result.valid is False
    assert any("object" in e.lower() for e in result.errors)


# ── Dry-Run Evaluator Tests (V0.8.4 backfill) ──────────────────────

def test_dry_run_evaluator_imports() -> None:
    from app.policies.evaluator import PolicyDryRunEvaluator
    assert PolicyDryRunEvaluator is not None


def test_dry_run_evaluator_always_allow() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "allow", "severity": "low"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "x"}},
    )
    assert result["valid"] is True
    assert result["final_action"] == "allow"
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["action"] == "allow"


def test_dry_run_evaluator_match_block() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "match", "match": {"field": "subject.content", "equals": "bad"}}, "action": "block", "severity": "high"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "bad"}},
    )
    assert result["final_action"] == "block"
    assert result["decisions"][0]["action"] == "block"


def test_dry_run_evaluator_expression_safe() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "expression", "expression": "len(x) > 5"}, "action": "block"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "hello"}},
    )
    # Expression not executed — returns require_review instead
    assert result["final_action"] == "require_review"
    assert result["decisions"][0]["metadata"].get("unsupported_expression") is True


def test_dry_run_evaluator_no_policies() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "x"}},
    )
    assert result["valid"] is True
    assert result["final_action"] == "allow"
    assert len(result["decisions"]) == 0


def test_dry_run_evaluator_block_wins() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "allow"},
                {"id": "r2", "condition": {"type": "always"}, "action": "block"},
                {"id": "r3", "condition": {"type": "always"}, "action": "warn"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "x"}},
    )
    assert result["final_action"] == "block"


def test_dry_run_evaluator_no_match_falls_to_default() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "match", "match": {"field": "subject.content", "equals": "nonexistent"}}, "action": "block"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "hello"}},
    )
    assert result["final_action"] == "allow"
    assert result["decisions"][0]["action"] == "allow"


def test_dry_run_evaluator_scope_filter() -> None:
    result = PolicyDryRunEvaluator.evaluate(
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "tool",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "block"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
        context={"context_id": "c1", "scope": "input", "subject": {"type": "msg", "content": "x"}},
    )
    # Policy scope is 'tool', context scope is 'input' — no match
    assert result["final_action"] == "allow"
    assert len(result["decisions"]) == 0


# ── Dry-Run Hook Tests (V0.8.6) ────────────────────────────────────

class _MockEventRepo:
    """Minimal mock that records create() calls for hook testing."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def create(self, **kwargs) -> None:
        self.events.append(kwargs)


def test_input_hook_noop_without_policies() -> None:
    """No policies means no guardrail event and sequence unchanged."""
    from app.policies.dry_run_hooks import run_input_guardrail

    repo = _MockEventRepo()
    seq = run_input_guardrail(
        task_input="hello",
        run_id="run_test",
        run_metadata={"module_id": "test"},
        trace_id="trace_test",
        sequence=5,
        event_repository=repo,
        policies=[],
        guardrails=[],
    )
    assert seq == 5  # unchanged
    assert len(repo.events) == 0  # no event recorded


def test_input_hook_records_event() -> None:
    """With policies, guardrail.dry_run.completed event is recorded."""
    from app.policies.dry_run_hooks import run_input_guardrail

    repo = _MockEventRepo()
    seq = run_input_guardrail(
        task_input="hello",
        run_id="run_test",
        run_metadata={"module_id": "test"},
        trace_id="trace_test",
        sequence=5,
        event_repository=repo,
        policies=[{
            "id": "allow_all",
            "name": "Allow All",
            "version": "1.0",
            "scope": "input",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "allow"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
    )
    assert seq == 6  # advanced
    assert len(repo.events) == 1
    event = repo.events[0]
    assert event["event_type"] == "guardrail.dry_run.completed"
    assert event["metadata"]["scope"] == "input"
    assert event["metadata"]["execution_mode"] == "dry_run"
    assert event["metadata"]["final_action"] == "allow"
    assert event["metadata"]["decision_count"] == 1


def test_input_hook_block_does_not_block() -> None:
    """Even with final_action=block, the run is not prevented."""
    from app.policies.dry_run_hooks import run_input_guardrail

    repo = _MockEventRepo()
    seq = run_input_guardrail(
        task_input="block_me",
        run_id="run_test",
        run_metadata={"module_id": "test"},
        trace_id="trace_test",
        sequence=5,
        event_repository=repo,
        policies=[{
            "id": "block_policy",
            "name": "Block Policy",
            "version": "1.0",
            "scope": "input",
            "rules": [
                {
                    "id": "r1",
                    "condition": {"type": "match", "match": {"field": "subject.content", "equals": "block_me"}},
                    "action": "block",
                    "severity": "high",
                },
            ],
            "default_action": "allow",
        }],
        guardrails=[],
    )
    assert seq == 6  # advanced (no crash)
    assert len(repo.events) == 1
    assert repo.events[0]["metadata"]["final_action"] == "block"


def test_input_hook_exception_safe() -> None:
    """Exception in hook should not crash — returns sequence unchanged."""
    from app.policies.dry_run_hooks import run_input_guardrail

    # Pass garbage that will cause evaluator to crash when accessed
    seq = run_input_guardrail(
        task_input="hello",
        run_id="run_test",
        run_metadata=None,  # type: ignore — will cause AttributeError
        trace_id="trace_test",
        sequence=5,
        event_repository=_MockEventRepo(),
        policies=[{
            "id": "p1", "name": "P1", "version": "1.0", "scope": "input",
            "rules": [{"id": "r1", "condition": {"type": "always"}, "action": "allow"}],
            "default_action": "allow",
        }],
    )
    # Should fall through to except and return sequence unchanged
    assert seq == 5


def test_run_flow_unaffected_by_hook() -> None:
    """Normal run via API still works with the hook wired in."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/runs", json={"input": "hello"})
    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "completed"
    assert run["output"] is not None
    # No guardrail event visible in default flow (no policies)
    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [e["event_type"] for e in events]
    assert "guardrail.dry_run.completed" not in event_types
    assert event_types[:2] == ["run.created", "run.started"]
    assert event_types[-1] == "run.completed"


# ── Tool Guardrail Hook Tests (V0.8.7) ─────────────────────────────

def test_tool_hook_noop_without_policies() -> None:
    """No policies means no guardrail event and sequence unchanged."""
    from app.policies.dry_run_hooks import run_tool_guardrail

    repo = _MockEventRepo()
    seq = run_tool_guardrail(
        tool_name="mock_echo",
        tool_arguments={"input": "hello"},
        run_id="run_test",
        trace_id="trace_test",
        span_id="span_test",
        sequence=10,
        event_repository=repo,
        policies=[],
        guardrails=[],
    )
    assert seq == 10  # unchanged
    assert len(repo.events) == 0  # no event recorded


def test_tool_hook_records_event() -> None:
    """With policies, guardrail.dry_run.completed event is recorded."""
    from app.policies.dry_run_hooks import run_tool_guardrail

    repo = _MockEventRepo()
    seq = run_tool_guardrail(
        tool_name="mock_echo",
        tool_arguments={"input": "hello"},
        run_id="run_test",
        trace_id="trace_test",
        span_id="span_test",
        sequence=10,
        event_repository=repo,
        policies=[{
            "id": "tool_allow",
            "name": "Tool Allow",
            "version": "1.0",
            "scope": "tool",
            "rules": [
                {"id": "r1", "condition": {"type": "always"}, "action": "allow"},
            ],
            "default_action": "allow",
        }],
        guardrails=[],
    )
    assert seq == 11  # advanced
    assert len(repo.events) == 1
    event = repo.events[0]
    assert event["event_type"] == "guardrail.dry_run.completed"
    assert event["metadata"]["scope"] == "tool"
    assert event["metadata"]["execution_mode"] == "dry_run"
    assert event["metadata"]["final_action"] == "allow"
    assert event["metadata"]["decision_count"] == 1
    assert event["metadata"]["tool_name"] == "mock_echo"


def test_tool_hook_block_does_not_block() -> None:
    """Even with final_action=block, tool execution is not prevented."""
    from app.policies.dry_run_hooks import run_tool_guardrail

    repo = _MockEventRepo()
    seq = run_tool_guardrail(
        tool_name="mock_echo",
        tool_arguments={"input": "block_test"},
        run_id="run_test",
        trace_id="trace_test",
        span_id="span_test",
        sequence=10,
        event_repository=repo,
        policies=[{
            "id": "tool_block",
            "name": "Tool Block",
            "version": "1.0",
            "scope": "tool",
            "rules": [
                {
                    "id": "r1",
                    "condition": {"type": "always"},
                    "action": "block",
                    "severity": "high",
                },
            ],
            "default_action": "allow",
        }],
        guardrails=[],
    )
    assert seq == 11  # advanced (no crash)
    assert len(repo.events) == 1
    assert repo.events[0]["metadata"]["final_action"] == "block"


def test_tool_hook_noop_in_pipeline() -> None:
    """Default pipeline run with no policies — no guardrail event."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    run = client.post("/api/runs", json={"input": "tool noop test"}).json()
    assert run["status"] == "completed"

    events = client.get(f"/api/runs/{run['id']}/events").json()
    event_types = [e["event_type"] for e in events]
    # No guardrail event in default flow
    assert "guardrail.dry_run.completed" not in event_types
    # Core event order preserved
    assert event_types[:2] == ["run.created", "run.started"]
    assert event_types[-1] == "run.completed"
    # Tool events still present
    assert "tool.call.started" in event_types
    assert "tool.call.completed" in event_types
