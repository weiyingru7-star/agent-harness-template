from pydantic import BaseModel, Field


class DemoAgentNodeTrace(BaseModel):
    name: str
    output: str
    status: str = "completed"
    error_type: str | None = None
    error_message: str | None = None
    state: dict = Field(default_factory=dict)


class DemoAgentState(BaseModel):
    input: str
    normalized_input: str | None = None
    skill_output: str | None = None
    tool_output: str | None = None
    final_output: str | None = None
    node_traces: list[DemoAgentNodeTrace] = Field(default_factory=list)
