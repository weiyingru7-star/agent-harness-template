from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProviderRef(BaseModel):
    provider_name: str = "mock"
    model: str | None = None
    config_ref: str | None = None


class ToolsConfig(BaseModel):
    allowed_tools: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)


class RagConfig(BaseModel):
    enabled: bool = False
    collection: str = "default"
    retrieval_mode: str = "keyword"


class WorkflowConfig(BaseModel):
    entrypoint: str | None = None
    nodes: list[Any] = Field(default_factory=list)
    edges: list[Any] = Field(default_factory=list)
    terminal_nodes: list[str] | None = None


class EvalConfig(BaseModel):
    cases_path: str | None = None
    required_checks: list[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    runtime_version: str = "v0.6.1"
    provider: str | ProviderRef = "mock"
    tools: list[str] | ToolsConfig = Field(default_factory=list)
    rag: RagConfig = Field(default_factory=lambda: RagConfig(enabled=False))
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)
    policies: list[dict] = Field(default_factory=list)
    guardrails: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @staticmethod
    def normalize_provider(v: str | ProviderRef | dict | None) -> ProviderRef:
        if v is None or isinstance(v, str):
            return ProviderRef(provider_name=v or "mock")
        if isinstance(v, ProviderRef):
            return v
        if isinstance(v, dict):
            return ProviderRef(**v)
        return ProviderRef()

    @staticmethod
    def normalize_tools(v: list[str] | ToolsConfig | dict | None) -> ToolsConfig:
        if v is None:
            return ToolsConfig()
        if isinstance(v, ToolsConfig):
            return v
        if isinstance(v, list):
            return ToolsConfig(allowed_tools=v, required_tools=list(v))
        if isinstance(v, dict):
            return ToolsConfig(**v)
        return ToolsConfig()
