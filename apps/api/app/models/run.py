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
    type: str = "node"
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    output: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None
    attempt: int = 1
    max_attempts: int = 1
    error_type: str | None = None
    error_message: str | None = None
    failed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class Run(BaseModel):
    id: str
    trace_id: str | None = None
    status: RunStatus
    task: Task
    steps: list[Step] = Field(default_factory=list)
    output: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    failed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class RunEvent(BaseModel):
    type: str
    message: str
    event_type: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    sequence: int | None = None
    status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class CreateRunRequest(BaseModel):
    input: str = Field(min_length=1)
    module_id: str | None = None


class TraceSpan(BaseModel):
    id: str
    trace_id: str | None = None
    run_id: str
    step_id: str
    parent_span_id: str | None = None
    name: str
    type: str
    status: StepStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None
    metadata: dict = Field(default_factory=dict)


class RunTrace(BaseModel):
    run_id: str
    trace_id: str | None = None
    spans: list[TraceSpan] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)


class TimelineItem(BaseModel):
    type: str
    label: str
    status: str | None = None
    step_id: str | None = None
    span_id: str | None = None
    tool_call_id: str | None = None
    checkpoint_id: str | None = None
    checkpoint_index: int | None = None
    sequence: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)


class RunTimeline(BaseModel):
    run_id: str
    trace_id: str | None = None
    status: RunStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    items: list[TimelineItem] = Field(default_factory=list)


class Checkpoint(BaseModel):
    id: str
    run_id: str
    step_id: str
    trace_id: str | None = None
    span_id: str | None = None
    checkpoint_index: int
    state: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ToolCall(BaseModel):
    id: str
    run_id: str
    step_id: str
    trace_id: str | None = None
    span_id: str | None = None
    tool_id: str
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
