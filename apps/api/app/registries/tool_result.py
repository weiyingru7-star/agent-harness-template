from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ToolResultStatus = Literal["completed", "failed"]


class ToolResult(BaseModel):
    status: ToolResultStatus
    output: str | None = None
    raw_output: Any = None
    summary: str | None = None
    artifacts: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None
