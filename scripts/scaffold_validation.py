"""Shared scaffold validation and hygiene utilities.

V0.9.5 — single source of truth for name validation, security checks,
and safe path resolution used by all scaffold scripts.
"""

import re
from pathlib import Path


# ── Constants ───────────────────────────────────────────────────────

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_NAME_LENGTH = 64

BUSINESS_TERMS: set[str] = {
    "ecommerce", "e_commerce", "电商", "客服", "cs",
    "服装", "clothing", "fashion",
    "订单", "order", "售后", "refund", "return",
    "cad", "灯具", "lighting",
    "报价", "quote", "pricing",
    "自媒体", "social_media", "influencer",
}

SENSITIVE_NAMES: set[str] = {
    "env", ".env", "secret", "secrets",
    "key", "keys", "token", "tokens",
    "credential", "credentials", "password",
    "config", ".config",
}


# ── Validation ──────────────────────────────────────────────────────


def validate_scaffold_name(name: str, kind: str = "scaffold") -> list[str]:
    """Validate a scaffold name, returning a list of error messages.

    Args:
        name: The name to validate.
        kind: Human-readable kind for error messages
              (e.g. "module", "agent", "eval case").

    Returns:
        List of error messages. Empty list means valid.
    """
    errors: list[str] = []
    label = kind.capitalize() if kind else "Scaffold"

    if not name:
        errors.append(f"{label} name is required.")
        return errors

    if len(name) > MAX_NAME_LENGTH:
        errors.append(
            f"{label} name too long ({len(name)} > {MAX_NAME_LENGTH} chars)."
        )

    if ".." in name or "/" in name or "\\" in name:
        errors.append(f"Path traversal detected in {label.lower()} name: '{name}'")

    if not NAME_PATTERN.fullmatch(name):
        errors.append(
            f"{label} name must use snake_case (lowercase letters, digits, underscores), "
            f"starting with a letter. Got: '{name}'"
        )

    if name.startswith("."):
        errors.append(f"{label} name cannot start with '.': '{name}'")

    lower = name.lower()
    if lower in SENSITIVE_NAMES:
        errors.append(f"{label} name '{name}' is reserved and cannot be used.")

    if lower in BUSINESS_TERMS:
        errors.append(
            f"{label} name '{name}' contains a business term. "
            f"Names must be business-neutral."
        )

    return errors


def resolve_safe_target(base_dir: Path, target_name: str) -> Path:
    """Resolve a target path under base_dir, preventing traversal.

    Args:
        base_dir: The allowed base directory.
        target_name: The filename or subdirectory name to resolve.

    Returns:
        Resolved absolute Path.

    Raises:
        RuntimeError: If the resolved path is outside base_dir.
    """
    try:
        target = (base_dir / target_name).resolve()
        resolved_base = base_dir.resolve()
    except (OSError, RuntimeError):
        target = (base_dir.absolute() / target_name)
        resolved_base = base_dir.absolute()

    try:
        target.relative_to(resolved_base)
    except ValueError:
        raise RuntimeError(
            f"Target path '{target}' is outside allowed directory "
            f"'{resolved_base}'. Refusing to proceed."
        )

    return target


def format_errors(errors: list[str]) -> str:
    """Format a list of error messages for stderr output."""
    if not errors:
        return ""
    return "\n".join(f"Error: {err}" for err in errors)
