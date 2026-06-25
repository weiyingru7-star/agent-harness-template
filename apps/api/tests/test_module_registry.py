from pathlib import Path

from harness.registries import AgentExecutionContext, ModuleRegistry


def test_module_registry_scans_demo_agent() -> None:
    registry = ModuleRegistry()

    modules = registry.list_modules()

    demo_agent = next(module for module in modules if module.id == "demo_agent")
    assert demo_agent.name == "Demo Agent"
    assert demo_agent.version == "0.1.0"
    assert demo_agent.entrypoint == "modules.demo_agent.agent:execute"
    assert demo_agent.enabled is True
    assert demo_agent.capabilities == ["demo", "state_machine"]
    assert demo_agent.default_agent == "demo_agent"
    assert demo_agent.agent is not None
    assert demo_agent.agent.provider == "mock"


def test_module_registry_skips_invalid_module(tmp_path: Path) -> None:
    invalid_module = tmp_path / "invalid_module"
    invalid_module.mkdir()
    (invalid_module / "module.yaml").write_text(
        "id: invalid_module\nname: Invalid Module\n",
        encoding="utf-8",
    )

    registry = ModuleRegistry(modules_dir=tmp_path)

    assert registry.list_modules() == []
    assert len(registry.warnings) == 1
    assert "Invalid module manifest" in registry.warnings[0].message


def test_module_registry_executes_demo_agent() -> None:
    registry = ModuleRegistry()
    context = AgentExecutionContext(
        module_id="demo_agent",
        agent_id="demo_agent",
        run_id="run_test",
    )

    result = registry.execute("demo_agent", "hello contract", context)

    assert result.output == (
        "demo_agent mock response | "
        "skill=Mock skill summary: hello contract | "
        "tool=Mock tool echo: Mock skill summary: hello contract"
    )
    assert [step.name for step in result.steps] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
