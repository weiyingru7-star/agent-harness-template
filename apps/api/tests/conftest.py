import os
from pathlib import Path
from tempfile import gettempdir

# ── Environment isolation ───────────────────────────────────────────
# Ensure all provider env vars use safe defaults before Settings()
# is imported. This prevents the user's shell env from leaking into
# tests (e.g. AI_PROVIDER=openai_compatible set in .env or shell).
_DEFAULT_AI_VARS = {
    "AI_PROVIDER": "mock",
    "AI_BASE_URL": "",
    "AI_API_KEY": "",
    "AI_MODEL": "gpt-4o-mini",
    "AI_TIMEOUT": "30",
    "AI_MAX_ATTEMPTS": "1",
    "AI_FALLBACK_PROVIDER": "mock",
    "AI_STREAMING_ENABLED": "true",
    "OPENAI_COMPATIBLE_BASE_URL": "",
    "OPENAI_COMPATIBLE_API_KEY": "",
    "OPENAI_COMPATIBLE_MODEL": "gpt-4o-mini",
}
for var, value in _DEFAULT_AI_VARS.items():
    os.environ[var] = value

TEST_ROOT = Path(gettempdir()) / "agent_harness_template_tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_ROOT / 'test_agent_harness.db'}")
os.environ.setdefault("LOCAL_STORAGE_DIR", str(TEST_ROOT / "uploads"))

import pytest

from core.db import reset_db


@pytest.fixture(autouse=True)
def clean_database() -> None:
    reset_db()
