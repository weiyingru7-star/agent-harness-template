from typing import Any

from pydantic import BaseModel, Field


class AgentStepTrace(BaseModel):
    name: str
    output: str
    status: str = "completed"
    error_type: str | None = None
    error_message: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionContext(BaseModel):
    module_id: str
    agent_id: str
    run_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResult(BaseModel):
    output: str
    steps: list[AgentStepTrace] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentManifest(BaseModel):
    id: str
    module_id: str
    name: str
    description: str
    system_prompt_path: str
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    workflow: str
    provider: str
    created_at: str | None = None
    updated_at: str | None = None


class ModuleManifest(BaseModel):
    id: str
    name: str
    version: str
    description: str
    entrypoint: str
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)
    default_agent: str
    created_at: str | None = None
    updated_at: str | None = None
    agent: AgentManifest | None = None
