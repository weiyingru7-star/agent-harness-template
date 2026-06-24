from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates" / "module-template"
MODULES_DIR = ROOT / "modules"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 cli/scaffold_module.py <module_name>", file=sys.stderr)
        return 2

    module_name = sys.argv[1]
    if not re.fullmatch(r"[a-z][a-z0-9_]*", module_name):
        print(
            "Module name must use lowercase letters, numbers, and underscores, "
            "and start with a letter.",
            file=sys.stderr,
        )
        return 2

    target_dir = MODULES_DIR / module_name
    if target_dir.exists():
        print(f"Module already exists: {target_dir}", file=sys.stderr)
        return 1

    module_title = module_name.replace("_", " ").title()
    replacements = {
        "{{module_name}}": module_name,
        "{{module_title}}": module_title,
    }

    scaffold_module(target_dir=target_dir, replacements=replacements)
    print(f"Created module: {target_dir}")
    return 0


def scaffold_module(target_dir: Path, replacements: dict[str, str]) -> None:
    for source_path in TEMPLATE_DIR.rglob("*"):
        relative_path = source_path.relative_to(TEMPLATE_DIR)
        rendered_parts = [
            render_text(part, replacements).replace("__module_name__", replacements["{{module_name}}"])
            for part in relative_path.parts
        ]
        target_path = target_dir.joinpath(*rendered_parts)

        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.name == ".gitkeep":
            shutil.copyfile(source_path, target_path)
            continue

        content = source_path.read_text(encoding="utf-8")
        target_path.write_text(render_text(content, replacements), encoding="utf-8")


def render_text(text: str, replacements: dict[str, str]) -> str:
    rendered = text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


if __name__ == "__main__":
    raise SystemExit(main())
