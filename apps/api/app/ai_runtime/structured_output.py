import json
from typing import Any


def parse_structured_output(output: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None
