import json
from typing import Any


class StructuredOutputError(ValueError):
    pass


def parse_structured_output(output: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def parse_structured_output_or_raise(output: str) -> dict[str, Any]:
    parsed = parse_structured_output(output)
    if parsed is None:
        raise StructuredOutputError("Structured output must be a JSON object")
    return parsed
