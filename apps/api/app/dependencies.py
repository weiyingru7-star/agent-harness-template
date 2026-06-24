from collections.abc import Iterator

from sqlalchemy.orm import Session

from core.db.session import get_db


def get_database_session() -> Iterator[Session]:
    yield from get_db()
