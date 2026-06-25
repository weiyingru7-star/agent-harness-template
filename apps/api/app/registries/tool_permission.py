from __future__ import annotations

from app.registries.tools import ToolDefinition


class PermissionResult:
    def __init__(
        self,
        allowed: bool,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.allowed = allowed
        self.error_type = error_type
        self.error_message = error_message


class ToolPermissionChecker:
    """Minimal permission checker for tool calls.

    Supports three permission levels:
      - safe:      always allowed (default).
      - restricted: allowed only when the run context is listed in
                    allowed_contexts.
      - blocked:   always denied.

    The `requires_approval` flag is reserved for future interactive
    approval flows and is ignored by this checker.
    """

    @staticmethod
    def check(
        tool_def: ToolDefinition,
        run_context: str | None = None,
    ) -> PermissionResult:
        level = tool_def.permission_level

        if level == "blocked":
            return PermissionResult(
                allowed=False,
                error_type="ToolPermissionDenied",
                error_message=(
                    f"Tool {tool_def.id} is blocked and cannot be used"
                ),
            )

        if level == "restricted":
            allowed_contexts = tool_def.allowed_contexts or []
            if run_context not in allowed_contexts:
                return PermissionResult(
                    allowed=False,
                    error_type="ToolPermissionDenied",
                    error_message=(
                        f"Tool {tool_def.id} is restricted "
                        f"to contexts: {allowed_contexts}; "
                        f"got '{run_context}'"
                    ),
                )
            return PermissionResult(allowed=True)

        return PermissionResult(allowed=True)
