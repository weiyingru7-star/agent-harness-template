from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UploadedFile(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    extension: str
    storage_path: str
    text: str
    created_at: datetime = Field(default_factory=utc_now)
