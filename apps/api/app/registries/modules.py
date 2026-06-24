from pydantic import BaseModel


class ModuleDefinition(BaseModel):
    id: str
    name: str
    description: str


MODULES = {
    "demo_agent": ModuleDefinition(
        id="demo_agent",
        name="Demo Agent",
        description="Minimal demo module that runs local mock skill and tool calls.",
    )
}


def list_modules() -> list[ModuleDefinition]:
    return list(MODULES.values())
