"""PolicyDryRunEvaluator — evaluates policies/guardrails against an EvaluationContext.

V0.8.4 — dry-run only, no enforcement, no runtime changes.
Produces a DecisionResult dict describing what *would* happen in enforcement mode.
"""

from __future__ import annotations

from app.policies.models import POLICY_ACTIONS, POLICY_SCOPES
from app.policies.validator import PolicyValidator


_ACTION_PRIORITY = {"block": 0, "require_review": 1, "warn": 2, "allow": 3}


def _merge_final_action(decisions: list[dict]) -> str:
    """Merge decisions: block > require_review > warn > allow."""
    if not decisions:
        return "allow"
    best = min(
        (d["action"] for d in decisions if d.get("action") in _ACTION_PRIORITY),
        key=lambda a: _ACTION_PRIORITY[a],
        default="allow",
    )
    return best


def _get_field(obj: dict, path: str):
    """Resolve dot-notation path into a nested dict value."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]
    return current


def _evaluate_condition(condition: dict, context: dict) -> tuple[bool, str | None]:
    """
    Evaluate a single condition against the context.
    Returns (matched, unsupported_reason).
    If unsupported_reason is set, matched is treated as True but with a warning.
    """
    ct = condition.get("type", "")
    if ct == "always":
        return True, None

    if ct == "match":
        match_cfg = condition.get("match", {})
        field = match_cfg.get("field", "")
        value = _get_field(context, field)

        if "equals" in match_cfg:
            return value == match_cfg["equals"], None
        if "contains" in match_cfg:
            return isinstance(value, str) and match_cfg["contains"] in value, None
        if "exists" in match_cfg:
            return (value is not None) == bool(match_cfg["exists"]), None
        # No valid operator — no match
        return False, None

    if ct == "route":
        route_key = condition.get("route_key", "")
        if route_key:
            attributes = context.get("attributes", {})
            return route_key in attributes, None
        return False, None

    if ct == "expression":
        return True, "unsupported_expression"

    return False, None


class PolicyDryRunEvaluator:
    """Evaluates policies/guardrails against an EvaluationContext.

    Dry-run only — produces a DecisionResult dict without intercepting
    real requests or modifying runtime state. Not a runtime enforcement engine.
    """

    @staticmethod
    def evaluate(
        *,
        policies: list[dict],
        guardrails: list[dict],
        context: dict,
    ) -> dict:
        """Run a dry-run evaluation and return a DecisionResult as a dict.

        Args:
            policies: List of policy dicts (same format as eval JSON).
            guardrails: List of guardrail dicts.
            context: EvaluationContext dict (V0.8.3 contract).

        Returns:
            DecisionResult dict with keys: valid, final_action, decisions,
            errors, warnings, error_items, metadata.
        """
        # 1. Validate inputs
        v_result = PolicyValidator.validate_policies(policies)
        if guardrails:
            policy_ids = {p.get("id", "") for p in policies}
            g_result = PolicyValidator.validate_guardrails(guardrails, policy_ids=policy_ids)
            v_result.errors.extend(g_result.errors)
            v_result.warnings.extend(g_result.warnings)
            v_result.error_items.extend(g_result.error_items)

        ctx_result = PolicyValidator.validate_evaluation_context(context)
        v_result.errors.extend(ctx_result.errors)
        v_result.warnings.extend(ctx_result.warnings)
        v_result.error_items.extend(ctx_result.error_items)

        if v_result.errors:
            return {
                "valid": False,
                "final_action": "allow",
                "decisions": [],
                "errors": v_result.errors,
                "warnings": v_result.warnings,
                "error_items": [e.model_dump() for e in v_result.error_items],
                "metadata": {},
            }

        context_scope = context.get("scope", "")
        decisions: list[dict] = []

        # 2. Build policy lookup
        policy_map: dict[str, dict] = {}
        for p in policies:
            pid = p.get("id", "")
            policy_map[pid] = p

        # 3. Process guardrails (or use all policies if no guardrails defined)
        if guardrails:
            eligible_guardrails = [
                g for g in guardrails
                if g.get("enabled", True)
                and g.get("type", "") == context_scope
            ]
        else:
            # No guardrails defined — evaluate all scope-matching policies
            eligible_guardrails = []

        if eligible_guardrails:
            for guardrail in eligible_guardrails:
                gid = guardrail.get("id", "")
                policy_ref = guardrail.get("policy_ref")
                if policy_ref:
                    if policy_ref in policy_map:
                        decisions.extend(
                            PolicyDryRunEvaluator._evaluate_policy(
                                policy_map[policy_ref], context, guardrail_id=gid,
                            )
                        )
                    else:
                        # policy_ref not found — error
                        decisions.append({
                            "decision_id": f"dry_run_g_{gid}_ref_missing",
                            "policy_id": policy_ref,
                            "guardrail_id": gid,
                            "action": "require_review",
                            "severity": "high",
                            "reason": f"Guardrail '{gid}' references unknown policy '{policy_ref}'",
                            "matched_rules": [],
                            "metadata": {"error": "policy_ref_not_found"},
                        })
                else:
                    # No policy_ref — evaluate all scope-matching policies
                    for p in policies:
                        if p.get("scope", "") == context_scope:
                            decisions.extend(
                                PolicyDryRunEvaluator._evaluate_policy(
                                    p, context, guardrail_id=gid,
                                )
                            )
        else:
            # No guardrails config — evaluate all scope-matching policies
            for p in policies:
                if p.get("scope", "") == context_scope:
                    decisions.extend(
                        PolicyDryRunEvaluator._evaluate_policy(p, context)
                    )

        # 4. Merge final_action
        final_action = _merge_final_action(decisions)

        return {
            "valid": True,
            "final_action": final_action,
            "decisions": decisions,
            "errors": [],
            "warnings": [],
            "error_items": [],
            "metadata": {"evaluator": "PolicyDryRunEvaluator", "version": "v0.8.4"},
        }

    @staticmethod
    def _evaluate_policy(
        policy: dict,
        context: dict,
        guardrail_id: str | None = None,
    ) -> list[dict]:
        """Evaluate a single policy against context, return list of decisions."""
        decisions: list[dict] = []
        policy_id = policy.get("id", "")
        scope = policy.get("scope", "")
        default_action = policy.get("default_action", "allow")
        rules: list[dict] = policy.get("rules", [])

        matched_any = False
        for rule in rules:
            condition = rule.get("condition", {})
            matched, unsupported = _evaluate_condition(condition, context)

            if matched:
                matched_any = True
                rule_action = rule.get("action", "warn")
                rule_severity = rule.get("severity", "medium")
                rule_message = rule.get("message", "")
                matched_rules = [rule.get("id", "unknown")]

                if unsupported == "unsupported_expression":
                    expr = condition.get("expression", "")
                    decisions.append({
                        "decision_id": f"dry_run_{policy_id}_unsupported_expr",
                        "policy_id": policy_id,
                        "guardrail_id": guardrail_id,
                        "action": "require_review",
                        "severity": "high",
                        "reason": f"Expression evaluation not supported in dry-run mode: '{expr}'",
                        "matched_rules": matched_rules,
                        "metadata": {"unsupported_expression": True, "expression": expr},
                    })
                else:
                    decisions.append({
                        "decision_id": f"dry_run_{policy_id}_{rule.get('id', 'unknown')}",
                        "policy_id": policy_id,
                        "guardrail_id": guardrail_id,
                        "action": rule_action,
                        "severity": rule_severity,
                        "reason": rule_message or f"Rule '{rule.get('id', '')}' matched in policy '{policy_id}'",
                        "matched_rules": matched_rules,
                        "metadata": {"scope": scope, "condition_type": condition.get("type", "")},
                    })

        if not matched_any:
            decisions.append({
                "decision_id": f"dry_run_{policy_id}_default",
                "policy_id": policy_id,
                "guardrail_id": guardrail_id,
                "action": default_action,
                "severity": "low",
                "reason": f"No rules matched in policy '{policy_id}', using default_action={default_action}",
                "matched_rules": [],
                "metadata": {"scope": scope, "default_action": default_action},
            })

        return decisions
