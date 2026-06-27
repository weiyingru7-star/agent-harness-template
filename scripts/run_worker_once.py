#!/usr/bin/env python3
"""Run one queued job (single-process MVP).

Usage:
    python3 scripts/run_worker_once.py

Not a daemon — processes one job and exits.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///data/worker.db")

from app.services.job_queue import job_queue  # noqa: E402
from app.services.worker_runtime import WorkerRuntime  # noqa: E402


def main() -> int:
    runtime = WorkerRuntime(job_queue)
    result = runtime.run_once()
    print(result)
    return 0 if result == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
