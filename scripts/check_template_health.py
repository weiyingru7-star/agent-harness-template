#!/usr/bin/env python3
"""Static template health check for Agent Harness Template.

Checks that key files exist, scaffold scripts are present, template
directories are intact, .env is not git-tracked, and no business
term contamination is found.

Exit codes:
  0 = healthy
  1 = failed (one or more checks did not pass)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Files that must exist in a healthy template
KEY_FILES = [
    "README.md",
    "QUICKSTART.md",
    "TEMPLATE_USAGE.md",
    "Makefile",
    "CLAUDE.md",
    "AGENTS.md",
    "docker-compose.yml",
    "scripts/check_business_terms.py",
]

SCAFFOLD_SCRIPTS = [
    "scripts/scaffold_module.py",
    "scripts/scaffold_agent.py",
    "scripts/scaffold_eval.py",
    "scripts/scaffold_docs.py",
    "scripts/scaffold_validation.py",
]

TEMPLATE_DIRS = [
    "templates/agent-template/agent.json",
    "templates/module-template/module.yaml",
]


def check() -> list[str]:
    """Run all health checks, return list of failure messages."""
    failures: list[str] = []

    # 1. Key files exist
    for path_str in KEY_FILES:
        if not (ROOT / path_str).is_file():
            failures.append(f"Missing key file: {path_str}")

    # 2. Scaffold scripts exist
    for path_str in SCAFFOLD_SCRIPTS:
        if not (ROOT / path_str).is_file():
            failures.append(f"Missing scaffold script: {path_str}")

    # 3. Template directories exist
    for path_str in TEMPLATE_DIRS:
        if not (ROOT / path_str).is_file():
            failures.append(f"Missing template file: {path_str}")

    # 4. .env is not git-tracked
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.returncode == 0:
            failures.append(".env is tracked by git — should be in .gitignore")
    except FileNotFoundError:
        failures.append("git not found — cannot check .env tracking")

    # 5. Business term contamination
    try:
        bt_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_business_terms.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        if bt_result.returncode != 0:
            failures.append(
                f"Business term contamination detected:\n{bt_result.stderr.strip()}"
            )
    except FileNotFoundError:
        failures.append("Could not run check_business_terms.py")

    return failures


def main() -> int:
    failures = check()

    if not failures:
        print("Template health: OK")
        return 0

    print(f"Template health: FAILED ({len(failures)} issue(s))", file=sys.stderr)
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
