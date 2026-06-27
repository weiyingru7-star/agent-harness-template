#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates" / "module-template"
MODULES_DIR = ROOT / "modules"

# ── Shared validation ──────────────────────────────────────────────

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from scaffold_validation import (  # noqa: E402
    validate_scaffold_name,
    resolve_safe_target,
)


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
    errors = validate_scaffold_name(name, kind="module")
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
        return 2

    # 2. Resolve target
    try:
        target_dir = resolve_safe_target(MODULES_DIR, name)
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
