#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUSINESS_TERMS = [
    "电商",
    "客服",
    "服装",
    "CAD",
    "商品",
    "订单",
    "售后",
    "自媒体",
    "竞品",
    "灯具",
    "报价",
]
DEFAULT_TARGETS = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "PROJECT_BOUNDARIES.md",
    "TASK_SPEC.md",
    "TESTING.md",
    "docs",
    "apps/web",
    "apps/api",
    "core",
    "ai_runtime",
    "harness",
    "schemas",
    "evals",
    "infra",
    "templates",
    "cli",
    "scripts",
]
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    "data",
}
ALLOWED_CONTEXT_MARKERS = [
    "BUSINESS_TERMS",
    "业务词",
    "禁止",
    "污染",
    "forbidden",
    "business term",
    "具体行业",
]
ALLOWED_FILES = {
    Path("scripts/check_business_terms.py"),
    Path("apps/api/tests/test_schema_contracts.py"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check core template files for business terms.")
    parser.add_argument("paths", nargs="*", help="Optional paths to scan.")
    args = parser.parse_args()

    targets = [ROOT / path for path in (args.paths or DEFAULT_TARGETS)]
    violations = []
    for file_path in iter_files(targets):
        violations.extend(check_file(file_path))

    if violations:
        for path, line_number, term, line in violations:
            relative_path = path.relative_to(ROOT)
            print(f"{relative_path}:{line_number}: found '{term}': {line.strip()}")
        return 1

    print("No business term contamination found.")
    return 0


def iter_files(targets: list[Path]):
    for target in targets:
        if not target.exists():
            continue
        if target.is_file():
            if should_scan(target):
                yield target
            continue
        for path in target.rglob("*"):
            if path.is_file() and should_scan(path):
                yield path


def should_scan(path: Path) -> bool:
    relative_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDED_PARTS for part in relative_parts):
        return False
    return path.suffix in {".md", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".toml"}


def check_file(path: Path) -> list[tuple[Path, int, str, str]]:
    findings = []
    if path.relative_to(ROOT) in ALLOWED_FILES:
        return findings

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return findings

    for line_number, line in enumerate(lines, start=1):
        for term in BUSINESS_TERMS:
            if term in line and not is_allowed_context(line):
                findings.append((path, line_number, term, line))
    return findings


def is_allowed_context(line: str) -> bool:
    return any(marker in line for marker in ALLOWED_CONTEXT_MARKERS)


if __name__ == "__main__":
    sys.exit(main())
