#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "evals" / "workflow_cases"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.registries.agent_config import WorkflowConfig  # noqa: E402
from app.registries.workflow_validator import WorkflowValidator  # noqa: E402


@dataclass
class WfEvalResult:
    case_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)


def load_cases() -> list[dict[str, Any]]:
    paths = sorted(CASE_DIR.glob("*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def run_case(case: dict[str, Any]) -> WfEvalResult:
    case_id = str(case.get("id", "unknown"))
    failures: list[str] = []

    wf_data = case.get("workflow", {})
    config = WorkflowConfig(**wf_data)
    result = WorkflowValidator.validate(config)

    if result.valid != case.get("expected_valid", True):
        failures.append(f"expected_valid={case.get('expected_valid')} got valid={result.valid}")

    expected_codes = case.get("expected_error_codes", [])
    actual_codes = {item.code for item in result.error_items if item.severity == "error"}
    for code in expected_codes:
        if code not in actual_codes:
            failures.append(f"expected error code '{code}' not found in result")

    return WfEvalResult(case_id=case_id, passed=not failures, failures=failures)


def main() -> int:
    cases = load_cases()
    if not cases:
        print(f"No workflow eval cases found in {CASE_DIR}")
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
