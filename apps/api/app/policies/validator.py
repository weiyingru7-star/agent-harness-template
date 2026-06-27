"""PolicyValidator — structural validation for Policy and Guardrail contracts.

V0.8.0 — validates structure only (scope, action, condition type). No
condition expressions are executed, no request interception, no runtime
changes.
"""

from __future__ import annotations

from app.policies.models import (
    CONDITION_TYPES,
    GUARDRAIL_TYPES,
    POLICY_ACTIONS,
    POLICY_SCOPES,
    RULE_SEVERITIES,
    PolicyValidationErrorItem,
    PolicyValidationResult,
)


ERROR_CODES: dict[str, str] = {
    "policy_id_missing": "POLICY_ID_MISSING",
    "scope_invalid": "POLICY_SCOPE_INVALID",
    "action_invalid": "POLICY_ACTION_INVALID",
    "rules_invalid": "POLICY_RULES_INVALID",
    "rule_id_missing": "POLICY_RULE_ID_MISSING",
    "rule_condition_missing": "POLICY_RULE_CONDITION_MISSING",
    "condition_type_invalid": "POLICY_CONDITION_TYPE_INVALID",
    "severity_invalid": "POLICY_SEVERITY_INVALID",
    "guardrail_id_missing": "GUARDRAIL_ID_MISSING",
    "guardrail_type_invalid": "GUARDRAIL_TYPE_INVALID",
    "guardrail_action_invalid": "GUARDRAIL_ACTION_INVALID",
    "guardrail_policy_ref_not_found": "GUARDRAIL_POLICY_REF_NOT_FOUND",
    # Decision contract codes (V0.8.2)
    "decision_id_missing": "DECISION_ID_MISSING",
    "decision_action_missing": "DECISION_ACTION_MISSING",
    "decision_action_invalid": "DECISION_ACTION_INVALID",
    "decision_severity_invalid": "DECISION_SEVERITY_INVALID",
    "decision_matched_rules_invalid": "DECISION_MATCHED_RULES_INVALID",
    "decision_result_final_action_invalid": "DECISION_RESULT_ACTION_INVALID",
    "decision_result_decisions_invalid": "DECISION_RESULT_DECISIONS_INVALID",
    # Evaluation context codes (V0.8.3)
    "context_id_missing": "CONTEXT_ID_MISSING",
    "context_scope_invalid": "CONTEXT_SCOPE_INVALID",
    "context_subject_missing": "CONTEXT_SUBJECT_MISSING",
    "context_subject_invalid": "CONTEXT_SUBJECT_INVALID",
    "context_subject_type_missing": "CONTEXT_SUBJECT_TYPE_MISSING",
    "context_attributes_invalid": "CONTEXT_ATTRIBUTES_INVALID",
}


class PolicyValidator:
    """Validates Policy and Guardrail structures.

    Each method returns a PolicyValidationResult with:
      - valid: bool
      - errors: list[str] (legacy flat list)
      - warnings: list[str]
      - error_items: list[PolicyValidationErrorItem] (structured items)

    No condition expressions are evaluated.
    """

    @staticmethod
    def validate_policies(policies: list[dict]) -> PolicyValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        items: list[PolicyValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
            ))

        def _warn(code: str, msg: str, path: str | None = None) -> None:
            warnings.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
                severity="warning",
            ))

        policy_ids: set[str] = set()
        for pi, policy in enumerate(policies):
            path = f"policies[{pi}]"
            pid = policy.get("id", "")
            if not pid:
                _err("policy_id_missing", f"{path}: policy id is required")
            else:
                policy_ids.add(pid)

            scope = policy.get("scope", "")
            if scope not in POLICY_SCOPES:
                _err("scope_invalid", f"{path}: invalid scope '{scope}'; allowed: {sorted(POLICY_SCOPES)}")

            action = policy.get("default_action", "allow")
            if action not in POLICY_ACTIONS:
                _err("action_invalid", f"{path}: invalid default_action '{action}'; allowed: {sorted(POLICY_ACTIONS)}")

            rules = policy.get("rules", [])
            if not isinstance(rules, list):
                _err("rules_invalid", f"{path}: rules must be a list")
                continue

            for ri, rule in enumerate(rules):
                rule_path = f"{path}.rules[{ri}]"
                if not isinstance(rule, dict):
                    _err("rules_invalid", f"{rule_path}: rule must be an object")
                    continue

                rid = rule.get("id")
                if not rid:
                    _err("rule_id_missing", f"{rule_path}: rule id is required")

                rule_action = rule.get("action", "warn")
                if rule_action not in POLICY_ACTIONS:
                    _err("action_invalid", f"{rule_path}.action: invalid action '{rule_action}'")

                rule_severity = rule.get("severity", "medium")
                if rule_severity not in RULE_SEVERITIES:
                    _err("severity_invalid", f"{rule_path}.severity: invalid severity '{rule_severity}'")

                condition = rule.get("condition")
                if not condition or not isinstance(condition, dict):
                    _err("rule_condition_missing", f"{rule_path}: rule condition is required")
                else:
                    ct = condition.get("type", "")
                    if ct not in CONDITION_TYPES:
                        _err("condition_type_invalid", f"{rule_path}.condition.type: invalid type '{ct}'; allowed: {sorted(CONDITION_TYPES)}")

        if not errors and not warnings:
            return PolicyValidationResult(valid=True)
        return PolicyValidationResult(valid=not bool(errors), errors=errors, warnings=warnings, error_items=items)

    @staticmethod
    def validate_guardrails(guardrails: list[dict], policy_ids: set[str] | None = None) -> PolicyValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        items: list[PolicyValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
            ))

        def _warn(code: str, msg: str, path: str | None = None) -> None:
            warnings.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
                severity="warning",
            ))

        for gi, guardrail in enumerate(guardrails):
            path = f"guardrails[{gi}]"
            if not isinstance(guardrail, dict):
                _err("guardrail_id_missing", f"{path}: guardrail must be an object")
                continue

            gid = guardrail.get("id", "")
            if not gid:
                _err("guardrail_id_missing", f"{path}: guardrail id is required")

            gt = guardrail.get("type", "")
            if gt not in GUARDRAIL_TYPES:
                _err("guardrail_type_invalid", f"{path}.type: invalid type '{gt}'; allowed: {sorted(GUARDRAIL_TYPES)}")

            action = guardrail.get("action", "allow")
            if action not in POLICY_ACTIONS:
                _err("guardrail_action_invalid", f"{path}.action: invalid action '{action}'")

            policy_ref = guardrail.get("policy_ref")
            if policy_ref and policy_ids is not None and policy_ref not in policy_ids:
                _warn("guardrail_policy_ref_not_found", f"{path}.policy_ref: referenced policy '{policy_ref}' not found in policy list")

        if not errors and not warnings:
            return PolicyValidationResult(valid=True)
        return PolicyValidationResult(valid=not bool(errors), errors=errors, warnings=warnings, error_items=items)

    # ── Decision contract validation (V0.8.2) ────────────────────────

    @staticmethod
    def validate_decision_contract(decision: dict) -> PolicyValidationResult:
        """Validate a single GuardrailDecision dict — structure only, no execution."""
        errors: list[str] = []
        warnings: list[str] = []
        items: list[PolicyValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
            ))

        if not isinstance(decision, dict):
            _err("decision_id_missing", "decision: must be an object")
            return PolicyValidationResult(valid=False, errors=errors, items=items)

        did = decision.get("decision_id")
        if not did:
            _err("decision_id_missing", "decision: decision_id is required")

        action = decision.get("action")
        if action is None:
            _err("decision_action_missing", "decision: action is required")
        elif action not in POLICY_ACTIONS:
            _err("decision_action_invalid", f"decision: invalid action '{action}'; allowed: {sorted(POLICY_ACTIONS)}")

        severity = decision.get("severity", "medium")
        if severity not in RULE_SEVERITIES:
            _err("decision_severity_invalid", f"decision: invalid severity '{severity}'; allowed: {sorted(RULE_SEVERITIES)}")

        matched_rules = decision.get("matched_rules", [])
        if not isinstance(matched_rules, list):
            _err("decision_matched_rules_invalid", "decision: matched_rules must be a list")

        if not errors and not warnings:
            return PolicyValidationResult(valid=True)
        return PolicyValidationResult(valid=not bool(errors), errors=errors, warnings=warnings, error_items=items)

    @staticmethod
    def validate_decision_result(result: dict) -> PolicyValidationResult:
        """Validate a DecisionResult dict — structure only, no execution."""
        errors: list[str] = []
        warnings: list[str] = []
        items: list[PolicyValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
            ))

        if not isinstance(result, dict):
            _err("decision_result_decisions_invalid", "decision_result: must be an object")
            return PolicyValidationResult(valid=False, errors=errors, items=items)

        final_action = result.get("final_action", "allow")
        if final_action not in POLICY_ACTIONS:
            _err("decision_result_final_action_invalid", f"decision_result: invalid final_action '{final_action}'; allowed: {sorted(POLICY_ACTIONS)}")

        decisions = result.get("decisions", [])
        if not isinstance(decisions, list):
            _err("decision_result_decisions_invalid", "decision_result: decisions must be a list")
        else:
            for di, d in enumerate(decisions):
                sub = PolicyValidator.validate_decision_contract(d)
                for item in sub.error_items:
                    item.path = f"decisions[{di}].{item.path}" if item.path else f"decisions[{di}]"
                errors.extend(sub.errors)
                warnings.extend(sub.warnings)
                items.extend(sub.error_items)

        if not errors and not warnings:
            return PolicyValidationResult(valid=True)
        return PolicyValidationResult(valid=not bool(errors), errors=errors, warnings=warnings, error_items=items)

    # ── Evaluation context validation (V0.8.3) ───────────────────────

    @staticmethod
    def validate_evaluation_context(context: dict) -> PolicyValidationResult:
        """Validate an EvaluationContext dict — structure only, no execution."""
        errors: list[str] = []
        warnings: list[str] = []
        items: list[PolicyValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(PolicyValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path,
            ))

        if not isinstance(context, dict):
            _err("context_id_missing", "evaluation_context: must be an object")
            return PolicyValidationResult(valid=False, errors=errors, items=items)

        cid = context.get("context_id")
        if not cid:
            _err("context_id_missing", "evaluation_context: context_id is required")

        scope = context.get("scope", "")
        if scope not in POLICY_SCOPES:
            _err("context_scope_invalid", f"evaluation_context: invalid scope '{scope}'; allowed: {sorted(POLICY_SCOPES)}")

        subject = context.get("subject")
        if subject is None:
            _err("context_subject_missing", "evaluation_context: subject is required")
        elif not isinstance(subject, dict):
            _err("context_subject_invalid", "evaluation_context: subject must be an object")
        else:
            st = subject.get("type")
            if not st:
                _err("context_subject_type_missing", "evaluation_context.subject: type is required")

        attributes = context.get("attributes", {})
        if not isinstance(attributes, dict):
            _err("context_attributes_invalid", "evaluation_context: attributes must be an object")

        if not errors and not warnings:
            return PolicyValidationResult(valid=True)
        return PolicyValidationResult(valid=not bool(errors), errors=errors, warnings=warnings, error_items=items)


policy_validator = PolicyValidator()
