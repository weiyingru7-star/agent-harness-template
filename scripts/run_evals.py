#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import gettempdir
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DEFAULT_CASE_DIR = ROOT / "evals" / "cases"
TEST_ROOT = Path(gettempdir()) / "agent_harness_template_evals"
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_ROOT / 'eval_agent_harness.db'}"
os.environ["LOCAL_STORAGE_DIR"] = str(TEST_ROOT / "uploads")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from core.db import reset_db  # noqa: E402


REQUIRED_FIELDS = [
    "id",
    "name",
    "module_id",
    "input",
    "expected_status",
    "expected_output_contains",
    "expected_events",
    "expected_steps",
    "expected_checkpoints_min",
    "expected_trace_spans_min",
    "expected_timeline_items_min",
    "expected_tool_calls_min",
    "metadata",
]


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)


def load_cases(case_paths: list[Path] | None = None) -> list[dict[str, Any]]:
    paths = case_paths or sorted(DEFAULT_CASE_DIR.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def validate_case(case: dict[str, Any]) -> list[str]:
    failures = [f"missing field: {field_name}" for field_name in REQUIRED_FIELDS if field_name not in case]
    if case.get("expected_status") not in {"completed", "failed"}:
        failures.append("expected_status must be completed or failed")
    for field_name in [
        "expected_output_contains",
        "expected_events",
        "expected_steps",
    ]:
        if field_name in case and not isinstance(case[field_name], list):
            failures.append(f"{field_name} must be a list")
    for field_name in [
        "expected_checkpoints_min",
        "expected_trace_spans_min",
        "expected_timeline_items_min",
        "expected_tool_calls_min",
    ]:
        if field_name in case and not isinstance(case[field_name], int):
            failures.append(f"{field_name} must be an integer")
    return failures


def run_eval_case(case: dict[str, Any], client: TestClient | None = None) -> EvalResult:
    case_id = str(case.get("id", "unknown"))
    failures = validate_case(case)
    if failures:
        return EvalResult(case_id=case_id, passed=False, failures=failures)

    test_client = client or TestClient(app)
    create_response = test_client.post(
        "/api/runs",
        json={"input": case["input"], "module_id": case["module_id"]},
    )
    if create_response.status_code != 201:
        return EvalResult(
            case_id=case_id,
            passed=False,
            failures=[f"POST /api/runs returned {create_response.status_code}"],
        )

    run = create_response.json()
    run_id = run["id"]
    events = _get_json(test_client, f"/api/runs/{run_id}/events", failures)
    trace = _get_json(test_client, f"/api/runs/{run_id}/trace", failures)
    checkpoints = _get_json(test_client, f"/api/runs/{run_id}/checkpoints", failures)
    timeline = _get_json(test_client, f"/api/runs/{run_id}/timeline", failures)
    tool_calls = _get_json(test_client, f"/api/runs/{run_id}/tool-calls", failures)

    _expect_equal("run.status", run["status"], case["expected_status"], failures)
    output = run.get("output") or ""
    for expected_text in case["expected_output_contains"]:
        if expected_text not in output:
            failures.append(f"run.output missing expected text: {expected_text}")

    event_types = {event.get("event_type") or event.get("type") for event in events}
    for expected_event in case["expected_events"]:
        if expected_event not in event_types:
            failures.append(f"events missing: {expected_event}")

    step_names = [step["name"] for step in run["steps"]]
    for expected_step in case["expected_steps"]:
        if expected_step not in step_names:
            failures.append(f"steps missing: {expected_step}")

    trace_spans = trace.get("spans", [])
    if len(trace_spans) < case["expected_trace_spans_min"]:
        failures.append(
            "trace.spans count "
            f"{len(trace_spans)} < {case['expected_trace_spans_min']}"
        )

    if len(checkpoints) < case["expected_checkpoints_min"]:
        failures.append(
            "checkpoints count "
            f"{len(checkpoints)} < {case['expected_checkpoints_min']}"
        )

    timeline_items = timeline.get("items", [])
    if len(timeline_items) < case["expected_timeline_items_min"]:
        failures.append(
            "timeline.items count "
            f"{len(timeline_items)} < {case['expected_timeline_items_min']}"
        )

    if len(tool_calls) < case["expected_tool_calls_min"]:
        failures.append(
            "tool_calls count "
            f"{len(tool_calls)} < {case['expected_tool_calls_min']}"
        )

    if case["expected_status"] == "failed":
        failed_steps = [step for step in run["steps"] if step["status"] == "failed"]
        if not failed_steps:
            failures.append("failed run has no failed step")
        elif not failed_steps[0].get("error_type"):
            failures.append("failed step missing error_type")
        failed_timeline_items = [
            item for item in timeline_items if item.get("status") == "failed"
        ]
        if not failed_timeline_items:
            failures.append("timeline missing failed item")
        elif not failed_timeline_items[0].get("error_type"):
            failures.append("failed timeline item missing error_type")

    return EvalResult(case_id=case_id, passed=not failures, failures=failures)


def run_eval_cases(cases: list[dict[str, Any]]) -> list[EvalResult]:
    reset_db()
    client = TestClient(app)
    return [run_eval_case(case, client=client) for case in cases]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run minimal Agent Harness eval cases.")
    parser.add_argument(
        "cases",
        nargs="*",
        type=Path,
        help="Optional eval case JSON files. Defaults to evals/cases/*.json.",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases or None)
    results = run_eval_cases(cases)
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.case_id}")
        for failure in result.failures:
            print(f"  - {failure}")

    print(f"Summary: {passed} passed, {failed} failed, {len(results)} total")
    return 0 if failed == 0 else 1


def _get_json(client: TestClient, path: str, failures: list[str]) -> Any:
    response = client.get(path)
    if response.status_code != 200:
        failures.append(f"{path} returned {response.status_code}")
        return {}
    return response.json()


def _expect_equal(field_name: str, actual: Any, expected: Any, failures: list[str]) -> None:
    if actual != expected:
        failures.append(f"{field_name} expected {expected}, got {actual}")


if __name__ == "__main__":
    raise SystemExit(main())
