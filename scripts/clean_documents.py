#!/usr/bin/env python3
"""Offline document cleaning pipeline.

Parses, cleans, and chunks raw documents for later ingestion.
Preview chunks are written for QA — final chunking happens at ingest time.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

# Ensure SQLite for offline CLI usage (no Postgres dependency)
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{ROOT / 'data' / 'pipeline_clean.db'}")

from harness.ingestion.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and chunk raw documents.")
    parser.add_argument("--tenant-id", required=True, help="Tenant ID for document tagging.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Input directory with raw documents.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output directory for cleaned docs.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.is_dir() and not args.dry_run:
        print(f"Error: input directory not found: {input_dir}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] Would process: {input_dir}")
        print(f"[dry-run] Would output: {output_dir}")

    run_pipeline(
        input_dir=input_dir,
        tenant_id=args.tenant_id,
        output_dir=output_dir,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
