import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_evals import REQUIRED_FIELDS, load_cases, run_eval_case, run_eval_cases  # noqa: E402


def test_eval_runner_passes_builtin_cases() -> None:
    results = run_eval_cases(load_cases())

    assert results
    assert all(result.passed for result in results)
    assert {result.case_id for result in results} == {
        "demo_agent_success",
        "demo_agent_failure",
        "demo_agent_invalid_tool_args",
        "demo_agent_tool_exception",
        "demo_agent_tool_timeout",
        "demo_agent_flaky_tool_retry",
        "demo_agent_tool_permission_denied",
    }


def test_eval_runner_identifies_failed_expectation() -> None:
    case = {
        "id": "expected_failure_detection",
        "name": "Expected Failure Detection",
        "module_id": "demo_agent",
        "input": "hello eval",
        "expected_status": "failed",
        "expected_output_contains": [],
        "expected_events": ["run.failed"],
        "expected_steps": ["missing_node"],
        "expected_checkpoints_min": 99,
        "expected_trace_spans_min": 99,
        "expected_timeline_items_min": 99,
        "expected_tool_calls_min": 99,
        "metadata": {},
    }

    result = run_eval_case(case)

    assert not result.passed
    assert any("run.status expected failed" in failure for failure in result.failures)
    assert any("events missing: run.failed" in failure for failure in result.failures)
    assert any("steps missing: missing_node" in failure for failure in result.failures)


def test_eval_cases_include_required_fields() -> None:
    for case_path in sorted((ROOT / "evals" / "cases").glob("*.json")):
        case = json.loads(case_path.read_text(encoding="utf-8"))
        for field in REQUIRED_FIELDS:
            assert field in case, f"{case_path.name} missing {field}"
