from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.registries.agent_config import WorkflowConfig


_WORKFLOW_NODE_TYPES = frozenset({"input", "provider", "tool", "rag", "decision", "final"})


class WorkflowNode(BaseModel):
    id: str
    type: str
    name: str | None = None
    config: dict = Field(default_factory=dict)
    next: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class WorkflowCondition(BaseModel):
    type: str = "always"
    expression: str | None = None
    route_key: str | None = None


class WorkflowEdge(BaseModel):
    from_node: str = Field(alias="from")
    to: str
    condition: WorkflowCondition | None = None
    metadata: dict = Field(default_factory=dict)


class WorkflowValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _collect_node_ids(nodes: list) -> set[str]:
    ids: set[str] = set()
    for node in nodes:
        if isinstance(node, str):
            ids.add(node)
        elif isinstance(node, dict):
            nid = node.get("id")
            if nid:
                ids.add(nid)
    return ids


class WorkflowValidator:
    @staticmethod
    def validate(config: WorkflowConfig) -> WorkflowValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        node_ids = _collect_node_ids(config.nodes)

        # entrypoint check (skip if it looks like a module path: contains '.' or ':')
        if config.entrypoint and "." not in config.entrypoint and ":" not in config.entrypoint:
            if config.entrypoint not in node_ids:
                errors.append(f"entrypoint '{config.entrypoint}' not found in nodes")

        # node id uniqueness
        seen: set[str] = set()
        for node in config.nodes:
            nid = node if isinstance(node, str) else (node.get("id") if isinstance(node, dict) else None)
            if nid and nid in seen:
                errors.append(f"duplicate node id '{nid}'")
            if nid:
                seen.add(nid)

        # node type validation (dict-formatted nodes only)
        for node in config.nodes:
            if isinstance(node, dict):
                nid = node.get("id", "")
                ntype = node.get("type", "")
                if ntype and ntype not in _WORKFLOW_NODE_TYPES:
                    errors.append(f"unsupported node type '{ntype}' for node '{nid}'")

        # edge validation
        for edge in config.edges:
            if isinstance(edge, list) and len(edge) >= 2:
                from_id, to_id = edge[0], edge[1]
                if from_id not in node_ids:
                    errors.append(f"edge references unknown node '{from_id}'")
                if to_id not in node_ids:
                    errors.append(f"edge references unknown node '{to_id}'")
                if from_id == to_id:
                    errors.append(f"edge from '{from_id}' to '{to_id}' is a self-loop")
            elif isinstance(edge, dict):
                from_id = edge.get("from", "")
                to_id = edge.get("to", "")
                if from_id not in node_ids:
                    errors.append(f"edge references unknown node '{from_id}'")
                if to_id not in node_ids:
                    errors.append(f"edge references unknown node '{to_id}'")

        # terminal_nodes check
        if config.terminal_nodes:
            for tn in config.terminal_nodes:
                if tn not in node_ids:
                    errors.append(f"terminal_nodes includes unknown node '{tn}'")

        return WorkflowValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
