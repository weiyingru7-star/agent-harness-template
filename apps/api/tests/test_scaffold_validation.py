"""Tests for V0.9.5 scripts/scaffold_validation.py shared utilities."""

from pathlib import Path

import pytest

from scripts.scaffold_validation import (
    BUSINESS_TERMS,
    MAX_NAME_LENGTH,
    NAME_PATTERN,
    SENSITIVE_NAMES,
    format_errors,
    resolve_safe_target,
    validate_scaffold_name,
)


# ── Validation: valid names ─────────────────────────────────────────


@pytest.mark.parametrize("valid_name", [
    "my_module", "test_agent", "simple", "a", "hello123", "my_eval_case",
])
def test_validate_valid_snake_case(valid_name: str) -> None:
    """Valid snake_case names pass validation."""
    errors = validate_scaffold_name(valid_name)
    assert errors == []


# ── Validation: invalid names ───────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "BadName", "123_name", "bad-name", "bad name", "",
])
def test_validate_uppercase_or_hyphen_rejected(bad_name: str) -> None:
    """Non-snake-case names are rejected."""
    assert len(validate_scaffold_name(bad_name)) > 0


def test_validate_dot_prefix_rejected() -> None:
    """Dot-prefixed names are rejected."""
    assert len(validate_scaffold_name(".test")) > 0


def test_validate_length_limit_rejected() -> None:
    """Names exceeding MAX_NAME_LENGTH are rejected."""
    long_name = "a" * (MAX_NAME_LENGTH + 1)
    errors = validate_scaffold_name(long_name)
    assert any("too long" in e.lower() for e in errors)


# ── Validation: path traversal ──────────────────────────────────────


@pytest.mark.parametrize("traversal", ["../x", "../../etc", "a/../../b", "..\\x"])
def test_validate_path_traversal_rejected(traversal: str) -> None:
    assert len(validate_scaffold_name(traversal)) > 0


# ── Validation: sensitive names ─────────────────────────────────────


@pytest.mark.parametrize("sensitive", sorted(SENSITIVE_NAMES))
def test_validate_sensitive_name_rejected(sensitive: str) -> None:
    errors = validate_scaffold_name(sensitive)
    assert any("reserved" in e.lower() for e in errors)


# ── Validation: business terms ──────────────────────────────────────


@pytest.mark.parametrize("term", sorted(BUSINESS_TERMS))
def test_validate_business_term_rejected(term: str) -> None:
    errors = validate_scaffold_name(term)
    assert any("business" in e.lower() for e in errors)


# ── Validation: kind parameter ──────────────────────────────────────


def test_validate_kind_in_message() -> None:
    """The kind parameter appears in error messages."""
    errors = validate_scaffold_name("", kind="module")
    assert any("Module" in e for e in errors)

    errors = validate_scaffold_name("", kind="agent")
    assert any("Agent" in e for e in errors)

    errors = validate_scaffold_name("", kind="eval case")
    # capitalize() on "eval case" → "Eval case"
    assert any("Eval case" in e for e in errors)


# ── resolve_safe_target ─────────────────────────────────────────────


def test_resolve_target_valid(tmp_path: Path) -> None:
    """Normal name resolves correctly under base_dir."""
    base = tmp_path / "base"
    base.mkdir()
    target = resolve_safe_target(base, "my_thing")
    assert str(target).endswith("my_thing")
    assert str(target).startswith(str(base))


def test_resolve_target_with_extension(tmp_path: Path) -> None:
    """Target name can include a file extension."""
    base = tmp_path / "evals"
    base.mkdir()
    target = resolve_safe_target(base, "my_case.json")
    assert str(target).endswith("my_case.json")


def test_resolve_target_outside_base_dir(tmp_path: Path) -> None:
    """Names that resolve outside base_dir raise RuntimeError."""
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(RuntimeError, match="outside"):
        resolve_safe_target(base, "../etc/passwd")


# ── format_errors ───────────────────────────────────────────────────


def test_format_errors_empty() -> None:
    assert format_errors([]) == ""


def test_format_errors_single() -> None:
    result = format_errors(["Something went wrong."])
    assert "Error: Something went wrong." in result


def test_format_errors_multiple() -> None:
    result = format_errors(["First error.", "Second error."])
    assert "Error: First error." in result
    assert "Error: Second error." in result
