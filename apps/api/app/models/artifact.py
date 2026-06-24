from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Artifact(BaseModel):
    id: str
    run_id: str
    file_id: str
    name: str
    kind: Literal["text"] = "text"
    text: str
    created_at: datetime = Field(default_factory=utc_now)


class CreateArtifactRequest(BaseModel):
    file_id: str
    name: str
