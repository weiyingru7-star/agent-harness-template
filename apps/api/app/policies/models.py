"""Policy / Guardrail / Rule / Condition data models — structural contracts only.

V0.8.0 — no execution logic, no request interception.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────

POLICY_SCOPES = {"input", "output", "tool", "rag", "provider", "workflow"}
POLICY_ACTIONS = {"allow", "block", "warn", "require_review"}
CONDITION_TYPES = {"always", "expression", "match", "route"}
RULE_SEVERITIES = {"low", "medium", "high", "critical"}
GUARDRAIL_TYPES = POLICY_SCOPES  # same set as policy scopes


# ── Error item (aligned with WorkflowValidationResult) ──────────────

class PolicyValidationErrorItem(BaseModel):
    code: str
    message: str
    path: str | None = None
    severity: str = "error"  # "error" or "warning"
    metadata: dict = Field(default_factory=dict)


class PolicyValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_items: list[PolicyValidationErrorItem] = Field(default_factory=list)


# ── Contracts ───────────────────────────────────────────────────────

class Condition(BaseModel):
    type: str  # Literal from CONDITION_TYPES, validated at runtime by validator
    expression: str | None = None
    match: dict | None = None
    route_key: str | None = None
    metadata: dict = Field(default_factory=dict)


class Rule(BaseModel):
    id: str
    condition: Condition
    action: str = "warn"  # from POLICY_ACTIONS
    severity: str = "medium"  # from RULE_SEVERITIES
    message: str = ""
    metadata: dict = Field(default_factory=dict)


class Policy(BaseModel):
    id: str
    name: str
    version: str
    scope: str  # from POLICY_SCOPES
    rules: list[Rule] = Field(default_factory=list)
    default_action: str = "allow"  # from POLICY_ACTIONS
    description: str = ""
    enabled: bool = True
    metadata: dict = Field(default_factory=dict)


class Guardrail(BaseModel):
    id: str
    name: str
    type: str  # from GUARDRAIL_TYPES (same as POLICY_SCOPES)
    enabled: bool = True
    policy_ref: str | None = None
    action: str = "allow"  # from POLICY_ACTIONS
    metadata: dict = Field(default_factory=dict)


# ── Decision Contracts (V0.8.2) ─────────────────────────────────────


class GuardrailDecision(BaseModel):
    decision_id: str
    policy_id: str | None = None
    guardrail_id: str | None = None
    action: str  # from POLICY_ACTIONS
    severity: str = "medium"  # from RULE_SEVERITIES
    reason: str = ""
    matched_rules: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class DecisionResult(BaseModel):
    valid: bool
    final_action: str = "allow"  # from POLICY_ACTIONS
    decisions: list[GuardrailDecision] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_items: list[PolicyValidationErrorItem] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


# ── Evaluation Context (V0.8.3) ─────────────────────────────────────


class EvaluationSubject(BaseModel):
    type: str
    id: str | None = None
    content: str | None = None
    payload: dict | None = None
    metadata: dict = Field(default_factory=dict)


class EvaluationContext(BaseModel):
    context_id: str
    scope: str  # from POLICY_SCOPES
    subject: EvaluationSubject
    attributes: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
