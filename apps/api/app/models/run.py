from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


RunStatus = Literal["pending", "running", "completed", "failed"]
StepStatus = Literal["pending", "running", "completed", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Task(BaseModel):
    id: str
    input: str
    created_at: datetime = Field(default_factory=utc_now)


class Step(BaseModel):
    id: str
    name: str
    status: StepStatus
    output: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class Run(BaseModel):
    id: str
    status: RunStatus
    task: Task
    steps: list[Step] = Field(default_factory=list)
    output: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class RunEvent(BaseModel):
    type: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class CreateRunRequest(BaseModel):
    input: str = Field(min_length=1)
    module_id: str | None = None
