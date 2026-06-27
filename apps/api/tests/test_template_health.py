"""Tests for V1.0 scripts/check_template_health.py.

These tests run against the real repository to verify health checks.
No temporary files are created in the repo.
"""

from pathlib import Path

import scripts.check_template_health as health


ROOT = Path(__file__).resolve().parents[3]


def test_health_key_files_exist() -> None:
    """All required key files are present."""
    for path_str in health.KEY_FILES:
        assert (ROOT / path_str).is_file(), f"Missing key file: {path_str}"


def test_health_scaffold_scripts_exist() -> None:
    """All scaffold scripts are present."""
    for path_str in health.SCAFFOLD_SCRIPTS:
        assert (ROOT / path_str).is_file(), f"Missing scaffold script: {path_str}"


def test_health_template_dirs_exist() -> None:
    """All required template files are present."""
    for path_str in health.TEMPLATE_DIRS:
        assert (ROOT / path_str).is_file(), f"Missing template file: {path_str}"


def test_health_check_returns_ok() -> None:
    """The check function returns empty list on a healthy repo."""
    failures = health.check()
    # Filter out git-related failures (git not available in all CI environments)
    non_git_failures = [f for f in failures if "git" not in f.lower()]
    assert non_git_failures == [], f"Health check failed: {non_git_failures}"


def test_health_main_exit_zero() -> None:
    """The main function exits with 0 on a healthy repo."""
    assert health.main() == 0


def test_health_calls_business_check() -> None:
    """check delegates to check_business_terms.py successfully."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_business_terms.py")],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, f"Business term check failed: {result.stderr}"
