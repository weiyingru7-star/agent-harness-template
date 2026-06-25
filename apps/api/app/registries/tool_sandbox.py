from __future__ import annotations

from app.registries.tools import ToolDefinition


class SandboxResult:
    def __init__(
        self,
        allowed: bool,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.allowed = allowed
        self.error_type = error_type
        self.error_message = error_message


class ToolSandboxChecker:
    """Minimal sandbox checker for tool execution.

    V0.3.6 checks execution_mode only:
      - in_process:    allowed (default)
      - disabled:      always denied
      - external_stub: denied (reserved for future sandbox executors)
    """

    @staticmethod
    def check(
        tool_def: ToolDefinition,
        context_args: dict | None = None,
    ) -> SandboxResult:
        mode = tool_def.execution_mode

        if mode != "in_process":
            return SandboxResult(
                allowed=False,
                error_type="ToolSandboxViolation",
                error_message=(
                    f"Tool {tool_def.id} ({mode}) execution not allowed"
                ),
            )

        return SandboxResult(allowed=True)
