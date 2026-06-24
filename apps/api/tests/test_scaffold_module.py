from pathlib import Path

import pytest

import cli.scaffold_module as scaffold_module


def test_scaffold_module_creates_valid_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules_dir = tmp_path / "modules"
    monkeypatch.setattr(scaffold_module, "MODULES_DIR", modules_dir)
    monkeypatch.setattr(scaffold_module.sys, "argv", ["scaffold_module.py", "sample_agent"])

    result = scaffold_module.main()

    assert result == 0
    assert (modules_dir / "sample_agent" / "module.yaml").is_file()
    assert (modules_dir / "sample_agent" / "agent.yaml").is_file()
    assert (modules_dir / "sample_agent" / "services" / "sample_agent_service.py").is_file()
    assert (modules_dir / "sample_agent" / "prompts" / "system.md").is_file()
    assert (modules_dir / "sample_agent" / "skills" / ".gitkeep").is_file()
    assert (modules_dir / "sample_agent" / "evals" / ".gitkeep").is_file()
    assert (modules_dir / "sample_agent" / "README.md").is_file()


@pytest.mark.parametrize("module_name", ["BadName", "123_agent", "bad-agent"])
def test_scaffold_module_rejects_invalid_module_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    monkeypatch.setattr(scaffold_module, "MODULES_DIR", tmp_path / "modules")
    monkeypatch.setattr(scaffold_module.sys, "argv", ["scaffold_module.py", module_name])

    assert scaffold_module.main() == 2


def test_scaffold_module_does_not_overwrite_existing_module(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules_dir = tmp_path / "modules"
    existing_module = modules_dir / "sample_agent"
    existing_module.mkdir(parents=True)
    marker = existing_module / "README.md"
    marker.write_text("existing", encoding="utf-8")

    monkeypatch.setattr(scaffold_module, "MODULES_DIR", modules_dir)
    monkeypatch.setattr(scaffold_module.sys, "argv", ["scaffold_module.py", "sample_agent"])

    assert scaffold_module.main() == 1
    assert marker.read_text(encoding="utf-8") == "existing"
