#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates" / "module-template"
MODULES_DIR = ROOT / "modules"

# ── Validation constants ────────────────────────────────────────────

MODULE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_NAME_LENGTH = 64

# Business term denylist (subset of scripts/check_business_terms.py).
# Will be unified with the hygiene checker in V0.9.5.
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


# ── Helpers ─────────────────────────────────────────────────────────


def validate_name(name: str) -> list[str]:
    """Validate module name, returning a list of error messages."""
    errors: list[str] = []

    if not name:
        errors.append("Module name is required.")
        return errors

    if len(name) > MAX_NAME_LENGTH:
        errors.append(f"Module name too long ({len(name)} > {MAX_NAME_LENGTH} chars).")

    if ".." in name or "/" in name or "\\" in name:
        errors.append(f"Path traversal detected in module name: '{name}'")

    if not MODULE_NAME_PATTERN.fullmatch(name):
        errors.append(
            f"Module name must use snake_case (lowercase letters, digits, underscores), "
            f"starting with a letter. Got: '{name}'"
        )

    if name.startswith("."):
        errors.append(f"Module name cannot start with '.': '{name}'")

    lower = name.lower()
    if lower in SENSITIVE_NAMES:
        errors.append(f"Module name '{name}' is reserved and cannot be used.")

    if lower in BUSINESS_TERMS:
        errors.append(
            f"Module name '{name}' contains a business term. "
            f"Module names must be business-neutral."
        )

    return errors


def resolve_target_path(name: str) -> Path:
    """Resolve and validate the target directory path.

    Ensures the resolved path is under MODULES_DIR to prevent
    path traversal outside the scaffold target area.
    """
    # Resolve symlinks and normalize
    try:
        target = (MODULES_DIR / name).resolve()
        modules_dir_resolved = MODULES_DIR.resolve()
    except (OSError, RuntimeError):
        # If resolution fails, use absolute path and verify
        target = MODULES_DIR.absolute() / name
        modules_dir_resolved = MODULES_DIR.absolute()

    # Safety check: target must be under MODULES_DIR
    try:
        target.relative_to(modules_dir_resolved)
    except ValueError:
        raise RuntimeError(
            f"Target path '{target}' is outside modules directory "
            f"'{modules_dir_resolved}'. Refusing to proceed."
        )

    return target


def collect_files(template_dir: Path, name: str) -> list[tuple[Path, Path]]:
    """Collect (source, target) pairs, substituting {{module_name}} in filenames."""
    files: list[tuple[Path, Path]] = []
    title = name.replace("_", " ").title()

    for source_path in sorted(template_dir.rglob("*")):
        if source_path.is_dir():
            continue
        relative = source_path.relative_to(template_dir)
        # Replace __module_name__ in path parts (for service filename)
        rendered_parts = [
            part.replace("__module_name__", name)
            for part in relative.parts
        ]
        target_name = source_path.name.replace("__module_name__", name)
        rendered_parts[-1] = target_name
        target_path = Path(*rendered_parts)
        files.append((source_path, target_path))

    return files


def render_content(content: str, name: str, title: str) -> str:
    content = content.replace("{{module_name}}", name)
    content = content.replace("{{module_title}}", title)
    return content


# ── Main scaffold logic ─────────────────────────────────────────────


def scaffold_module(name: str, target_dir: Path, dry_run: bool = False) -> int:
    """Create module skeleton at target_dir from template."""
    title = name.replace("_", " ").title()
    files = collect_files(TEMPLATE_DIR, name)

    if dry_run:
        _print_generated(files, name)
        print("\n[dry-run] No files were written.")
        return 0

    for source_path, target_path in files:
        full_target = target_dir / target_path
        full_target.parent.mkdir(parents=True, exist_ok=True)

        if source_path.name == ".gitkeep":
            shutil.copyfile(source_path, full_target)
        else:
            content = source_path.read_text(encoding="utf-8")
            rendered = render_content(content, name, title)
            full_target.write_text(rendered, encoding="utf-8")

    _print_generated(files, name)
    _print_next_steps(name)
    return 0


def _print_generated(files: list[tuple[Path, Path]], name: str) -> None:
    print(f"Generated files:")
    for _, target_path in files:
        print(f"  modules/{name}/{target_path}")


def _print_next_steps(name: str) -> None:
    print(f"""
Next steps:
  - Review generated files: modules/{name}/
  - Run backend tests: make test-api
  - Stage new module: git add modules/{name}
""")


# ── CLI entry point ─────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Agent Harness module.",
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Module name in snake_case (e.g. sample_module).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target directory.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Alias for --dry-run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    name = args.name.strip()
    dry_run = args.dry_run or args.preview

    # 1. Validate name
    errors = validate_name(name)
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
        return 2

    # 2. Resolve target
    try:
        target_dir = resolve_target_path(name)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    # 3. Check existence
    if target_dir.exists():
        if not args.force:
            print(
                f"Error: Module already exists at {target_dir}. "
                f"Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1
        # Remove existing content before regenerating (only under modules/<name>/)
        shutil.rmtree(target_dir)

    # 4. Scaffold!
    return scaffold_module(name, target_dir, dry_run=dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
