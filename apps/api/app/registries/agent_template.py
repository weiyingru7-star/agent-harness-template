from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.registries.agent_config import AgentConfig


class AgentTemplate(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    provider: str = "mock"
    tools: list[str] = Field(default_factory=list)
    rag_collection: str | None = None
    workflow: str = "default"
    eval_cases: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    config: dict | None = None


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    runtime_version: str = ""
    provider_name: str = "mock"
    tools_count: int = 0
    rag_enabled: bool = False
    workflow_type: str = "default"
    nodes_count: int = 0
    eval_cases_path: str | None = None
    metadata: dict = Field(default_factory=dict)


class ValidateResult(BaseModel):
    template_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = Field(default_factory=dict)


_DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[4] / "templates" / "agent-template"


class AgentTemplateRegistry:
    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._templates_dir = Path(templates_dir) if templates_dir else _DEFAULT_TEMPLATES_DIR
        self._templates: dict[str, AgentTemplate] = {}
        self._configs: dict[str, AgentConfig] = {}
        self._scan()

    def _scan(self) -> None:
        if not self._templates_dir.exists():
            return
        for path in sorted(self._templates_dir.rglob("agent.json")):
            config = self._load_config(path)
            if config is not None:
                self._configs[config.id] = config
                self._templates[config.id] = self._config_to_template(config)

    def _load_config(self, path: Path) -> AgentConfig | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AgentConfig(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            warnings.warn(f"Invalid agent template: {path}: {exc}", stacklevel=2)
            return None

    @staticmethod
    def _extract_provider(config: AgentConfig) -> str:
        if isinstance(config.provider, str):
            return config.provider
        return config.provider.provider_name

    @staticmethod
    def _extract_tools(config: AgentConfig) -> list[str]:
        if isinstance(config.tools, list):
            return config.tools
        return config.tools.allowed_tools

    @staticmethod
    def _config_to_template(config: AgentConfig) -> AgentTemplate:
        provider = AgentTemplateRegistry._extract_provider(config)
        tools = AgentTemplateRegistry._extract_tools(config)
        return AgentTemplate(
            id=config.id,
            name=config.name,
            description=config.description,
            version=config.version,
            provider=provider,
            tools=tools,
            rag_collection=config.rag.collection if config.rag.enabled else None,
            workflow=config.workflow.entrypoint or "default",
            eval_cases=[],
            metadata=config.metadata,
            config=config.model_dump(),
        )

    def list_templates(self) -> list[AgentTemplate]:
        return list(self._templates.values())

    def list_summaries(self) -> list[TemplateSummary]:
        return [self._to_summary(c) for c in self._configs.values()]

    def get_template(self, template_id: str) -> AgentTemplate | None:
        return self._templates.get(template_id)

    def get_config(self, template_id: str) -> AgentConfig | None:
        return self._configs.get(template_id)

    def validate_template(self, template_id: str) -> ValidateResult:
        config = self.get_config(template_id)
        if config is None:
            return ValidateResult(
                template_id=template_id,
                valid=False,
                errors=[f"Template not found: {template_id}"],
            )
        return ValidateResult(
            template_id=template_id,
            valid=True,
        )

    @staticmethod
    def _to_summary(config: AgentConfig) -> TemplateSummary:
        provider = AgentTemplateRegistry._extract_provider(config)
        if isinstance(config.tools, list):
            tools_count = len(config.tools)
        else:
            tools_count = len(config.tools.allowed_tools)
        nodes_count = len(config.workflow.nodes)
        return TemplateSummary(
            id=config.id,
            name=config.name,
            description=config.description,
            version=config.version,
            runtime_version=config.runtime_version,
            provider_name=provider,
            tools_count=tools_count,
            rag_enabled=config.rag.enabled,
            workflow_type=config.workflow.entrypoint or "default",
            nodes_count=nodes_count,
            eval_cases_path=config.eval.cases_path,
            metadata=config.metadata,
        )

    @staticmethod
    def validate_json(content: str) -> list[str]:
        errors: list[str] = []
        try:
            data = json.loads(content)
            AgentConfig(**data)
        except json.JSONDecodeError as exc:
            errors.append(f"JSON parse error: {exc}")
        except ValidationError as exc:
            errors.extend(f"validation error: {e}" for e in exc.errors())
        return errors
