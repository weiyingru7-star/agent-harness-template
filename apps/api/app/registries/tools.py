from collections.abc import Callable

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    args_schema: dict | None = None


def mock_echo(args: dict) -> str:
    return f"Mock tool echo: {args['input']}"


MOCK_ECHO_ARGS_SCHEMA: dict = {
    "type": "object",
    "required": ["input"],
    "properties": {
        "input": {"type": "string"},
    },
}

TOOLS: dict[str, tuple[ToolDefinition, Callable[[dict], str]]] = {
    "mock_echo": (
        ToolDefinition(
            id="mock_echo",
            name="Mock Echo",
            description="Echoes local input for demo_agent.",
            args_schema=MOCK_ECHO_ARGS_SCHEMA,
        ),
        mock_echo,
    ),
}


def list_tools() -> list[ToolDefinition]:
    return [definition for definition, _handler in TOOLS.values()]


def get_tool(tool_id: str) -> Callable[[dict], str]:
    return TOOLS[tool_id][1]


def get_tool_definition(tool_id: str) -> ToolDefinition | None:
    entry = TOOLS.get(tool_id)
    if entry is None:
        return None
    return entry[0]
