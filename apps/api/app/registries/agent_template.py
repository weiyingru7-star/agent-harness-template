from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError


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


_DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[4] / "templates" / "agent-template"


class AgentTemplateRegistry:
    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._templates_dir = Path(templates_dir) if templates_dir else _DEFAULT_TEMPLATES_DIR
        self._templates: dict[str, AgentTemplate] = {}
        self._scan()

    def _scan(self) -> None:
        if not self._templates_dir.exists():
            return
        for path in sorted(self._templates_dir.rglob("agent.json")):
            template = self._load(path)
            if template is not None:
                self._templates[template.id] = template

    def _load(self, path: Path) -> AgentTemplate | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AgentTemplate(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            warnings.warn(f"Invalid agent template: {path}: {exc}", stacklevel=2)
            return None

    def list_templates(self) -> list[AgentTemplate]:
        return list(self._templates.values())

    def get_template(self, template_id: str) -> AgentTemplate | None:
        return self._templates.get(template_id)

    @staticmethod
    def validate_json(content: str) -> list[str]:
        errors: list[str] = []
        try:
            data = json.loads(content)
            AgentTemplate(**data)
        except json.JSONDecodeError as exc:
            errors.append(f"JSON parse error: {exc}")
        except ValidationError as exc:
            errors.extend(f"validation error: {e}" for e in exc.errors())
        return errors
