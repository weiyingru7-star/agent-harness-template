from collections.abc import Callable

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str


def mock_echo(tool_input: str) -> str:
    return f"Mock tool echo: {tool_input}"


TOOLS: dict[str, tuple[ToolDefinition, Callable[[str], str]]] = {
    "mock_echo": (
        ToolDefinition(
            id="mock_echo",
            name="Mock Echo",
            description="Echoes local input for demo_agent.",
        ),
        mock_echo,
    )
}


def list_tools() -> list[ToolDefinition]:
    return [definition for definition, _handler in TOOLS.values()]


def get_tool(tool_id: str) -> Callable[[str], str]:
    return TOOLS[tool_id][1]
