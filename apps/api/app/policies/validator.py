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


policy_validator = PolicyValidator()
