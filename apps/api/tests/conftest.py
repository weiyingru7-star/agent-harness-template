import os
from pathlib import Path
from tempfile import gettempdir

TEST_ROOT = Path(gettempdir()) / "agent_harness_template_tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_ROOT / 'test_agent_harness.db'}")
os.environ.setdefault("LOCAL_STORAGE_DIR", str(TEST_ROOT / "uploads"))

import pytest

from core.db import reset_db


@pytest.fixture(autouse=True)
def clean_database() -> None:
    reset_db()
