"""Tests for V0.9.4 scripts/scaffold_docs.py.

All tests use tmp_path — never writes to the real docs/scaffolds/ directory.
"""

from pathlib import Path

import pytest

import scripts.scaffold_docs as scaffold


def _run(args: list[str]) -> int:
    return scaffold.main(args)


@pytest.fixture(autouse=True)
def _isolate_target_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect DOCS_SCAFFOLDS_DIR to a temp path for all tests."""
    test_dir = tmp_path / "docs" / "scaffolds"
    test_dir.mkdir(parents=True)
    monkeypatch.setattr(scaffold, "DOCS_SCAFFOLDS_DIR", test_dir)
    return test_dir


# ── Valid name — all kinds ──────────────────────────────────────────


def test_scaffold_docs_module_kind() -> None:
    """kind=module creates a markdown file with module content."""
    assert _run(["--name", "my_module", "--kind", "module"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "module-my_module.md"
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "Module Scaffold" in content
    assert "module.yaml" in content


def test_scaffold_docs_agent_kind() -> None:
    """kind=agent creates a markdown file with agent content."""
    assert _run(["--name", "my_agent", "--kind", "agent"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "agent-my_agent.md"
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "Agent Scaffold" in content
    assert "agent.json" in content


def test_scaffold_docs_eval_kind() -> None:
    """kind=eval creates a markdown file with eval content."""
    assert _run(["--name", "my_eval", "--kind", "eval"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "eval-my_eval.md"
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "Eval Scaffold" in content
    assert "evals/cases" in content


def test_scaffold_docs_generic_kind() -> None:
    """kind=generic creates a generic markdown file."""
    assert _run(["--name", "my_thing", "--kind", "generic"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "generic-my_thing.md"
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "Generic Scaffold" in content


# ── Invalid kind ────────────────────────────────────────────────────


def test_scaffold_docs_invalid_kind_rejected() -> None:
    """argparse rejects invalid kind values via SystemExit."""
    import sys
    try:
        _run(["--name", "x", "--kind", "database"])
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 2


# ── No placeholders ─────────────────────────────────────────────────


def test_scaffold_docs_no_placeholders() -> None:
    """No {name} or {{placeholder}} markers remain."""
    assert _run(["--name", "clean_doc", "--kind", "generic"]) == 0
    content = (scaffold.DOCS_SCAFFOLDS_DIR / "generic-clean_doc.md").read_text(encoding="utf-8")
    assert "{" not in content


# ── Business-neutral content ────────────────────────────────────────


def test_scaffold_docs_neutral_content() -> None:
    """Generated docs do not contain API keys or business terms."""
    assert _run(["--name", "neutral_check", "--kind", "module"]) == 0
    content = (scaffold.DOCS_SCAFFOLDS_DIR / "module-neutral_check.md").read_text(encoding="utf-8")
    assert "API_KEY" not in content
    assert "api_key" not in content


# ── Invalid snake_case ──────────────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "BadName", "123_name", "bad-name", "bad name", "",
])
def test_scaffold_docs_invalid_name_rejected(bad_name: str) -> None:
    assert _run(["--name", bad_name]) == 2


# ── Path traversal ──────────────────────────────────────────────────


@pytest.mark.parametrize("traversal", ["../x", "../../etc", "a/../../b", "..\\x"])
def test_scaffold_docs_path_traversal_rejected(traversal: str) -> None:
    assert _run(["--name", traversal]) == 2


# ── Sensitive name ──────────────────────────────────────────────────


@pytest.mark.parametrize("sensitive", [".env", "secret", "key", "token", "password", "credentials"])
def test_scaffold_docs_sensitive_name_rejected(sensitive: str) -> None:
    assert _run(["--name", sensitive]) == 2


# ── Business term ───────────────────────────────────────────────────


def test_scaffold_docs_business_term_rejected() -> None:
    assert _run(["--name", "ecommerce"]) == 2
    assert _run(["--name", "order"]) == 2
    assert _run(["--name", "refund"]) == 2


# ── Dry-run ─────────────────────────────────────────────────────────


def test_scaffold_docs_dry_run_does_not_write() -> None:
    assert _run(["--name", "my_doc", "--dry-run"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "generic-my_doc.md"
    assert not target.exists()


def test_scaffold_docs_preview_alias_is_dry_run() -> None:
    assert _run(["--name", "my_doc", "--preview"]) == 0
    target = scaffold.DOCS_SCAFFOLDS_DIR / "generic-my_doc.md"
    assert not target.exists()


# ── Overwrite rules ─────────────────────────────────────────────────


def test_scaffold_docs_existing_rejected() -> None:
    assert _run(["--name", "existing"]) == 0  # create it
    assert (scaffold.DOCS_SCAFFOLDS_DIR / "generic-existing.md").exists()
    assert _run(["--name", "existing"]) == 1  # rejected


def test_scaffold_docs_force_overwrites() -> None:
    assert _run(["--name", "overwrite_me"]) == 0  # create
    target = scaffold.DOCS_SCAFFOLDS_DIR / "generic-overwrite_me.md"
    assert target.is_file()
    assert _run(["--name", "overwrite_me", "--force"]) == 0  # force
    assert target.is_file()
