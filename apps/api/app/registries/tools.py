from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from app.registries.tool_result import ToolResult


class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    args_schema: dict | None = None
    timeout_ms: int | None = None


def mock_echo(args: dict) -> ToolResult:
    input_text = args["input"]
    if input_text == "__TOOL_EXCEPTION__":
        raise RuntimeError("mock_echo intentional exception for test")
    if input_text == "__SLOW_TOOL__":
        import time
        time.sleep(10)

    output = f"Mock tool echo: {input_text}"
    return ToolResult(
        status="completed",
        output=output,
        raw_output=output,
        summary=f"Echoed: '{input_text}'",
        metadata={"char_count": len(input_text)},
    )


MOCK_ECHO_ARGS_SCHEMA: dict = {
    "type": "object",
    "required": ["input"],
    "properties": {
        "input": {"type": "string"},
    },
}

TOOLS: dict[str, tuple[ToolDefinition, Callable[[dict], ToolResult]]] = {
    "mock_echo": (
        ToolDefinition(
            id="mock_echo",
            name="Mock Echo",
            description="Echoes local input for demo_agent.",
            args_schema=MOCK_ECHO_ARGS_SCHEMA,
            timeout_ms=1000,
        ),
        mock_echo,
    ),
}


def list_tools() -> list[ToolDefinition]:
    return [definition for definition, _handler in TOOLS.values()]


def get_tool(tool_id: str) -> Callable[[dict], ToolResult]:
    return TOOLS[tool_id][1]


def get_tool_definition(tool_id: str) -> ToolDefinition | None:
    entry = TOOLS.get(tool_id)
    if entry is None:
        return None
    return entry[0]
