"""Tests for V0.9.1 scripts/scaffold_module.py.

All tests use tmp_path — never writes to the real modules/ directory.
"""

from pathlib import Path
from shutil import copytree

import pytest

import scripts.scaffold_module as scaffold


def _run(args: list[str]) -> int:
    """Run scaffold_module.main() with given args, return exit code."""
    return scaffold.main(args)


@pytest.fixture(autouse=True)
def _isolate_modules_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect MODULES_DIR to a temp path for all tests."""
    test_modules = tmp_path / "modules"
    test_modules.mkdir()
    monkeypatch.setattr(scaffold, "MODULES_DIR", test_modules)
    return test_modules


# ── Valid name ──────────────────────────────────────────────────────


def test_scaffold_valid_name_creates_files(tmp_path: Path) -> None:
    """A valid snake_case name creates all expected files."""
    assert _run(["--name", "my_module"]) == 0
    target = scaffold.MODULES_DIR / "my_module"
    assert (target / "module.yaml").is_file()
    assert (target / "agent.yaml").is_file()
    assert (target / "README.md").is_file()
    assert (target / "services" / "my_module_service.py").is_file()
    assert (target / "prompts" / "system.md").is_file()


def test_scaffold_valid_name_renders_placeholders(tmp_path: Path) -> None:
    """Generated YAML contains the correct module_name substitute."""
    assert _run(["--name", "sample_agent"]) == 0
    manifest = (scaffold.MODULES_DIR / "sample_agent" / "module.yaml").read_text(encoding="utf-8")
    assert "sample_agent" in manifest
    assert "{{module_name}}" not in manifest


# ── Invalid snake_case ──────────────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "BadName",        # uppercase
    "123_agent",      # starts with digit
    "bad-agent",      # hyphen
    "bad name",       # space
    "",               # empty
])
def test_scaffold_invalid_snake_case_rejected(bad_name: str) -> None:
    """Non-snake-case module names are rejected."""
    assert _run(["--name", bad_name]) == 2


# ── Path traversal ──────────────────────────────────────────────────


@pytest.mark.parametrize("traversal", [
    "../x",
    "../../etc",
    "a/../../b",
    "..\\x",
])
def test_scaffold_path_traversal_rejected(traversal: str) -> None:
    """Path traversal in module name is rejected."""
    assert _run(["--name", traversal]) == 2


# ── Sensitive name ──────────────────────────────────────────────────


@pytest.mark.parametrize("sensitive", [
    ".env", "secret", "key", "token", "password", "credentials",
])
def test_scaffold_sensitive_name_rejected(sensitive: str) -> None:
    """Sensitive/reserved names are rejected."""
    assert _run(["--name", sensitive]) == 2


# ── Business term ───────────────────────────────────────────────────


def test_scaffold_business_term_rejected() -> None:
    """Business terms in module name are rejected."""
    assert _run(["--name", "ecommerce"]) == 2
    assert _run(["--name", "order"]) == 2
    assert _run(["--name", "refund"]) == 2


# ── Dry-run ─────────────────────────────────────────────────────────


def test_scaffold_dry_run_does_not_write(tmp_path: Path) -> None:
    """Dry-run mode prints output but does not create any files."""
    assert _run(["--name", "my_module", "--dry-run"]) == 0
    target = scaffold.MODULES_DIR / "my_module"
    assert not target.exists()


def test_scaffold_preview_alias_is_dry_run(tmp_path: Path) -> None:
    """--preview is an alias for --dry-run."""
    assert _run(["--name", "my_module", "--preview"]) == 0
    target = scaffold.MODULES_DIR / "my_module"
    assert not target.exists()


# ── Overwrite rules ─────────────────────────────────────────────────


def test_scaffold_existing_target_rejected(tmp_path: Path) -> None:
    """Existing target directory without --force is rejected."""
    assert _run(["--name", "existing"]) == 0  # create it
    assert (scaffold.MODULES_DIR / "existing").exists()
    # Second attempt without --force should fail
    assert _run(["--name", "existing"]) == 1


def test_scaffold_force_overwrites(tmp_path: Path) -> None:
    """--force overwrites existing target directory."""
    assert _run(["--name", "overwrite_me"]) == 0  # create it
    marker = scaffold.MODULES_DIR / "overwrite_me" / "marker.txt"
    marker.write_text("old", encoding="utf-8")
    assert marker.is_file()

    # Force overwrite
    assert _run(["--name", "overwrite_me", "--force"]) == 0
    # Old file should be gone (directory was recreated from template)
    assert not marker.exists()
    # New files should exist
    assert (scaffold.MODULES_DIR / "overwrite_me" / "module.yaml").is_file()
