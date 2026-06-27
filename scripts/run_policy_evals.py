#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "evals" / "policy_cases"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.policies import PolicyValidator  # noqa: E402


@dataclass
class PolicyEvalResult:
    case_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)


def load_cases() -> list[dict[str, Any]]:
    paths = sorted(CASE_DIR.glob("*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def run_case(case: dict[str, Any]) -> PolicyEvalResult:
    case_id = str(case.get("name", "unknown"))
    failures: list[str] = []
    case_type = case.get("type", "policy_validation")

    if case_type == "decision_contract":
        decision = case.get("decision", {})
        p_result = PolicyValidator.validate_decision_contract(decision)
    elif case_type == "decision_result":
        result_obj = case.get("decision_result", {})
        p_result = PolicyValidator.validate_decision_result(result_obj)
    else:
        # policy_validation (default) — validate policies + guardrails
        policies = case.get("policies", [])
        guardrails = case.get("guardrails", [])
        p_result = PolicyValidator.validate_policies(policies)
        if guardrails:
            policy_ids = {p.get("id", "") for p in policies}
            g_result = PolicyValidator.validate_guardrails(guardrails, policy_ids=policy_ids)
            p_result.errors.extend(g_result.errors)
            p_result.warnings.extend(g_result.warnings)
            p_result.error_items.extend(g_result.error_items)

    combined_valid = not bool(p_result.errors)

    if combined_valid != case.get("expected_valid", True):
        failures.append(
            f"expected_valid={case.get('expected_valid')} got valid={combined_valid}"
        )

    expected_codes = case.get("expected_error_codes", [])
    actual_error_codes = {
        item.code for item in p_result.error_items if item.severity == "error"
    }
    for code in expected_codes:
        if code not in actual_error_codes:
            failures.append(f"expected error code '{code}' not found in result")

    expected_warning_codes = case.get("expected_warning_codes", [])
    actual_warning_codes = {
        item.code for item in p_result.error_items if item.severity == "warning"
    }
    for code in expected_warning_codes:
        if code not in actual_warning_codes:
            failures.append(f"expected warning code '{code}' not found in result")

    return PolicyEvalResult(case_id=case_id, passed=not failures, failures=failures)


def main() -> int:
    cases = load_cases()
    if not cases:
        print(f"No policy eval cases found in {CASE_DIR}")
        return 1

    results = [run_case(c) for c in cases]
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{status} {r.case_id}")
        for f in r.failures:
            print(f"  - {f}")

    print(f"Summary: {passed} passed, {failed} failed, {len(results)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
