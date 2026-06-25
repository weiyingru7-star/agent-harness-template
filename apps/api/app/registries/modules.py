from pydantic import BaseModel

from harness.registries import ModuleRegistry


class ModuleDefinition(BaseModel):
    id: str
    name: str
    version: str
    description: str
    capabilities: list[str]
    enabled: bool
    default_agent: str


def list_modules() -> list[ModuleDefinition]:
    return [
        ModuleDefinition(
            id=module.id,
            name=module.name,
            version=module.version,
            description=module.description,
            capabilities=module.capabilities,
            enabled=module.enabled,
            default_agent=module.default_agent,
        )
        for module in ModuleRegistry().list_modules()
    ]


def get_module(module_id: str):
    return ModuleRegistry().get_module(module_id)


def execute_module(module_id: str, task_input: str, run_id: str):
    module = ModuleRegistry().get_module(module_id)
    if module is None:
        raise ValueError(f"Module not found or disabled: {module_id}")

    from harness.registries import AgentExecutionContext

    context = AgentExecutionContext(
        module_id=module.id,
        agent_id=module.default_agent,
        run_id=run_id,
    )
    return ModuleRegistry().execute(module.id, task_input, context)
