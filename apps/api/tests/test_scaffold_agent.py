"""Tests for V0.9.2 scripts/scaffold_agent.py.

All tests use tmp_path — never writes to the real templates/ directory.
"""

import json
from pathlib import Path

import pytest

import scripts.scaffold_agent as scaffold


def _run(args: list[str]) -> int:
    """Run scaffold_agent.main() with given args, return exit code."""
    return scaffold.main(args)


@pytest.fixture(autouse=True)
def _isolate_target_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect TARGET_TEMPLATES_DIR to a temp path for all tests."""
    test_templates = tmp_path / "templates"
    test_templates.mkdir()
    monkeypatch.setattr(scaffold, "TARGET_TEMPLATES_DIR", test_templates)
    return test_templates


# ── Valid name ──────────────────────────────────────────────────────


def test_scaffold_agent_valid_name_creates_files() -> None:
    """A valid snake_case name creates agent.json and README.md."""
    assert _run(["--name", "my_agent"]) == 0
    target = scaffold.TARGET_TEMPLATES_DIR / "my_agent"
    assert (target / "agent.json").is_file()
    assert (target / "README.md").is_file()


def test_scaffold_agent_generated_json_valid() -> None:
    """Generated agent.json is valid JSON."""
    assert _run(["--name", "test_agent"]) == 0
    content = (scaffold.TARGET_TEMPLATES_DIR / "test_agent" / "agent.json").read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert isinstance(parsed, dict)
    assert parsed["id"] == "test_agent"
    assert parsed["name"] == "Test Agent"


def test_scaffold_agent_config_parsable_as_agentconfig() -> None:
    """Generated JSON can be loaded by AgentConfig."""
    from app.registries.agent_config import AgentConfig

    assert _run(["--name", "parsable_agent"]) == 0
    content = (scaffold.TARGET_TEMPLATES_DIR / "parsable_agent" / "agent.json").read_text(encoding="utf-8")
    data = json.loads(content)
    config = AgentConfig(**data)
    assert config.id == "parsable_agent"
    assert config.provider.provider_name == "mock"


def test_scaffold_agent_no_placeholders_remaining() -> None:
    """No {{name}} or {{title}} placeholders remain in output."""
    assert _run(["--name", "clean_agent"]) == 0
    content = (scaffold.TARGET_TEMPLATES_DIR / "clean_agent" / "agent.json").read_text(encoding="utf-8")
    assert "{{" not in content


# ── Invalid snake_case ──────────────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "BadName", "123_agent", "bad-agent", "bad name", "",
])
def test_scaffold_agent_invalid_name_rejected(bad_name: str) -> None:
    assert _run(["--name", bad_name]) == 2


# ── Path traversal ──────────────────────────────────────────────────


@pytest.mark.parametrize("traversal", ["../x", "../../etc", "a/../../b", "..\\x"])
def test_scaffold_agent_path_traversal_rejected(traversal: str) -> None:
    assert _run(["--name", traversal]) == 2


# ── Sensitive name ──────────────────────────────────────────────────


@pytest.mark.parametrize("sensitive", [".env", "secret", "key", "token", "password", "credentials"])
def test_scaffold_agent_sensitive_name_rejected(sensitive: str) -> None:
    assert _run(["--name", sensitive]) == 2


# ── Business term ───────────────────────────────────────────────────


def test_scaffold_agent_business_term_rejected() -> None:
    assert _run(["--name", "ecommerce"]) == 2
    assert _run(["--name", "order"]) == 2
    assert _run(["--name", "refund"]) == 2


# ── Dry-run ─────────────────────────────────────────────────────────


def test_scaffold_agent_dry_run_does_not_write() -> None:
    assert _run(["--name", "my_agent", "--dry-run"]) == 0
    target = scaffold.TARGET_TEMPLATES_DIR / "my_agent"
    assert not target.exists()


def test_scaffold_agent_preview_alias_is_dry_run() -> None:
    assert _run(["--name", "my_agent", "--preview"]) == 0
    target = scaffold.TARGET_TEMPLATES_DIR / "my_agent"
    assert not target.exists()


# ── Overwrite rules ─────────────────────────────────────────────────


def test_scaffold_agent_existing_rejected() -> None:
    assert _run(["--name", "existing"]) == 0  # create it
    assert (scaffold.TARGET_TEMPLATES_DIR / "existing").exists()
    assert _run(["--name", "existing"]) == 1  # rejected


def test_scaffold_agent_force_overwrites() -> None:
    assert _run(["--name", "overwrite_me"]) == 0  # create
    marker = scaffold.TARGET_TEMPLATES_DIR / "overwrite_me" / "old.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("old", encoding="utf-8")
    assert marker.is_file()
    # Force overwrite
    assert _run(["--name", "overwrite_me", "--force"]) == 0
    assert not marker.exists()
    assert (scaffold.TARGET_TEMPLATES_DIR / "overwrite_me" / "agent.json").is_file()
