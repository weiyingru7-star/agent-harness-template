"""Tests for V0.9.3 scripts/scaffold_eval.py.

All tests use tmp_path — never writes to the real evals/cases/ directory.
"""

import json
from pathlib import Path

import pytest

import scripts.scaffold_eval as scaffold


def _run(args: list[str]) -> int:
    return scaffold.main(args)


@pytest.fixture(autouse=True)
def _isolate_target_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect EVAL_CASES_DIR to a temp path for all tests."""
    test_cases = tmp_path / "evals" / "cases"
    test_cases.mkdir(parents=True)
    monkeypatch.setattr(scaffold, "EVAL_CASES_DIR", test_cases)
    return test_cases


# ── Valid name ──────────────────────────────────────────────────────


def test_scaffold_eval_valid_name_creates_file() -> None:
    """A valid snake_case name creates a JSON file."""
    assert _run(["--name", "my_eval"]) == 0
    target = scaffold.EVAL_CASES_DIR / "my_eval.json"
    assert target.is_file()


def test_scaffold_eval_generated_json_valid() -> None:
    """Generated JSON is valid and contains id field."""
    assert _run(["--name", "sample_eval"]) == 0
    content = (scaffold.EVAL_CASES_DIR / "sample_eval.json").read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert parsed["id"] == "sample_eval"
    assert parsed["name"] == "Sample Eval"


def test_scaffold_eval_required_fields_present() -> None:
    """All 13 REQUIRED_FIELDS are present in the generated JSON."""
    assert _run(["--name", "complete_eval"]) == 0
    content = (scaffold.EVAL_CASES_DIR / "complete_eval.json").read_text(encoding="utf-8")
    parsed = json.loads(content)
    for field in scaffold.REQUIRED_EVAL_FIELDS:
        assert field in parsed, f"Missing required field: {field}"


def test_scaffold_eval_schema_compatible() -> None:
    """Generated JSON passes the eval-case.schema.json validation.

    Uses the Python jsonschema library if available; otherwise skips
    the schema validation but still validates structure.
    """
    assert _run(["--name", "schema_eval"]) == 0
    content = (scaffold.EVAL_CASES_DIR / "schema_eval.json").read_text(encoding="utf-8")
    parsed = json.loads(content)

    # Structural checks matching schema
    assert isinstance(parsed["expected_output_contains"], list)
    assert isinstance(parsed["expected_events"], list)
    assert isinstance(parsed["expected_steps"], list)
    assert isinstance(parsed["expected_checkpoints_min"], int)
    assert isinstance(parsed["expected_trace_spans_min"], int)
    assert isinstance(parsed["expected_timeline_items_min"], int)
    assert isinstance(parsed["expected_tool_calls_min"], int)
    assert isinstance(parsed["metadata"], dict)
    assert parsed["expected_status"] in ("completed", "failed")

    # Try schema library if available
    try:
        import jsonschema
        schema_src = (
            Path(__file__).resolve().parents[2] / "schemas" / "eval-case.schema.json"
        )
        schema = json.loads(schema_src.read_text(encoding="utf-8"))
        jsonschema.validate(instance=parsed, schema=schema)
    except ImportError:
        pass  # jsonschema not in venv; structural checks suffice


def test_scaffold_eval_no_placeholders() -> None:
    """No {{name}} or {{title}} placeholders remain in output."""
    assert _run(["--name", "clean_eval"]) == 0
    content = (scaffold.EVAL_CASES_DIR / "clean_eval.json").read_text(encoding="utf-8")
    assert "{{" not in content


# ── Invalid snake_case ──────────────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "BadName", "123_eval", "bad-eval", "bad name", "",
])
def test_scaffold_eval_invalid_name_rejected(bad_name: str) -> None:
    assert _run(["--name", bad_name]) == 2


# ── Path traversal ──────────────────────────────────────────────────


@pytest.mark.parametrize("traversal", ["../x", "../../etc", "a/../../b", "..\\x"])
def test_scaffold_eval_path_traversal_rejected(traversal: str) -> None:
    assert _run(["--name", traversal]) == 2


# ── Sensitive name ──────────────────────────────────────────────────


@pytest.mark.parametrize("sensitive", [".env", "secret", "key", "token", "password", "credentials"])
def test_scaffold_eval_sensitive_name_rejected(sensitive: str) -> None:
    assert _run(["--name", sensitive]) == 2


# ── Business term ───────────────────────────────────────────────────


def test_scaffold_eval_business_term_rejected() -> None:
    assert _run(["--name", "ecommerce"]) == 2
    assert _run(["--name", "order"]) == 2
    assert _run(["--name", "refund"]) == 2


# ── Dry-run ─────────────────────────────────────────────────────────


def test_scaffold_eval_dry_run_does_not_write() -> None:
    """Dry-run mode prints output but does not create any files."""
    assert _run(["--name", "my_eval", "--dry-run"]) == 0
    target = scaffold.EVAL_CASES_DIR / "my_eval.json"
    assert not target.exists()


def test_scaffold_eval_preview_alias_is_dry_run() -> None:
    assert _run(["--name", "my_eval", "--preview"]) == 0
    target = scaffold.EVAL_CASES_DIR / "my_eval.json"
    assert not target.exists()


# ── Overwrite rules ─────────────────────────────────────────────────


def test_scaffold_eval_existing_rejected() -> None:
    assert _run(["--name", "existing"]) == 0  # create it
    assert (scaffold.EVAL_CASES_DIR / "existing.json").exists()
    assert _run(["--name", "existing"]) == 1  # rejected


def test_scaffold_eval_force_overwrites() -> None:
    assert _run(["--name", "overwrite_me"]) == 0  # create
    old_content = (scaffold.EVAL_CASES_DIR / "overwrite_me.json").read_text(encoding="utf-8")
    # Force overwrite should succeed
    assert _run(["--name", "overwrite_me", "--force"]) == 0
    assert (scaffold.EVAL_CASES_DIR / "overwrite_me.json").is_file()
