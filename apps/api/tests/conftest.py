import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./data/test_agent_harness.db")
os.environ.setdefault("LOCAL_STORAGE_DIR", "data/test_uploads")

import pytest

from core.db import reset_db


@pytest.fixture(autouse=True)
def clean_database() -> None:
    reset_db()
