from __future__ import annotations

import json
import warnings
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
    def _config_to_template(config: AgentConfig) -> AgentTemplate:
        if isinstance(config.provider, str):
            provider = config.provider
        else:
            provider = config.provider.provider_name

        if isinstance(config.tools, list):
            tools = config.tools
        else:
            tools = config.tools.allowed_tools

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

    def get_template(self, template_id: str) -> AgentTemplate | None:
        return self._templates.get(template_id)

    def get_config(self, template_id: str) -> AgentConfig | None:
        return self._configs.get(template_id)

    def validate_template(self, template_id: str) -> list[str]:
        errors: list[str] = []
        config = self.get_config(template_id)
        if config is None:
            errors.append(f"Template not found: {template_id}")
        return errors

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
