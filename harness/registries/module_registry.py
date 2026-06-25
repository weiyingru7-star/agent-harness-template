from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from harness.registries.types import (
    AgentExecutionContext,
    AgentExecutionResult,
    ModuleManifest,
)


ROOT = Path(__file__).resolve().parents[2]
MODULES_DIR = ROOT / "modules"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistryWarning:
    module_path: Path
    message: str


class ModuleRegistry:
    def __init__(self, modules_dir: Path = MODULES_DIR) -> None:
        self.modules_dir = modules_dir
        self.warnings: list[RegistryWarning] = []

    def list_modules(self) -> list[ModuleManifest]:
        modules: list[ModuleManifest] = []
        self.warnings = []

        if not self.modules_dir.exists():
            return modules

        for module_dir in sorted(path for path in self.modules_dir.iterdir() if path.is_dir()):
            manifest = self._load_module(module_dir)
            if manifest is not None and manifest.enabled:
                modules.append(manifest)

        return modules

    def get_module(self, module_id: str) -> ModuleManifest | None:
        for manifest in self.list_modules():
            if manifest.id == module_id:
                return manifest
        return None

    def execute(
        self,
        module_id: str,
        task_input: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        manifest = self.get_module(module_id)
        if manifest is None:
            raise ValueError(f"Module not found or disabled: {module_id}")

        entrypoint = self._load_entrypoint(manifest.entrypoint)
        result = entrypoint(task_input, context)
        if isinstance(result, AgentExecutionResult):
            return result
        if isinstance(result, str):
            return AgentExecutionResult(output=result)
        if isinstance(result, dict):
            return AgentExecutionResult.model_validate(result)

        raise TypeError("Agent entrypoint must return AgentExecutionResult, dict, or str")

    def _load_module(self, module_dir: Path) -> ModuleManifest | None:
        module_path = module_dir / "module.yaml"
        agent_path = module_dir / "agent.yaml"
        if not module_path.exists():
            return None

        try:
            module_data = self._read_yaml(module_path)
            agent_data = self._read_yaml(agent_path) if agent_path.exists() else None
            if agent_data is not None:
                module_data["agent"] = agent_data
            return ModuleManifest.model_validate(module_data)
        except (OSError, yaml.YAMLError, ValidationError, ValueError) as exc:
            self._warn(module_dir, f"Invalid module manifest: {exc}")
            return None

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Manifest must be a mapping: {path}")
        return data

    @staticmethod
    def _load_entrypoint(entrypoint: str) -> Callable[[str, AgentExecutionContext], AgentExecutionResult]:
        if ":" not in entrypoint:
            raise ValueError("Module entrypoint must use module.path:function format")

        module_path, function_name = entrypoint.split(":", 1)
        module = importlib.import_module(module_path)
        function = getattr(module, function_name)
        if not callable(function):
            raise TypeError(f"Module entrypoint is not callable: {entrypoint}")
        return function

    def _warn(self, module_path: Path, message: str) -> None:
        warning = RegistryWarning(module_path=module_path, message=message)
        self.warnings.append(warning)
        logger.warning("%s: %s", module_path, message)
