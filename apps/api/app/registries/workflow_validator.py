from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.registries.agent_config import WorkflowConfig


_WORKFLOW_NODE_TYPES = frozenset({"input", "provider", "tool", "rag", "decision", "final"})
_WORKFLOW_CONDITION_TYPES = frozenset({"always", "expression", "route", "on_success", "on_failure"})
_RAG_RETRIEVAL_MODES = frozenset({"keyword", "vector", "hybrid"})

BUILTIN_NODE_CONTRACTS: dict[str, dict[str, Any]] = {
    "input": {
        "allowed_config_keys": {"input_schema", "default"},
        "expected_inputs": [],
        "expected_outputs": ["payload"],
    },
    "provider": {
        "allowed_config_keys": {"provider_name", "model", "prompt_template", "temperature"},
        "expected_inputs": ["prompt"],
        "expected_outputs": ["output", "usage"],
    },
    "tool": {
        "allowed_config_keys": {"tool_name", "args_template"},
        "expected_inputs": ["input"],
        "expected_outputs": ["result", "status"],
    },
    "rag": {
        "allowed_config_keys": {"collection", "retrieval_mode", "query_template", "limit"},
        "expected_inputs": ["query"],
        "expected_outputs": ["results", "citations"],
    },
    "decision": {
        "allowed_config_keys": {"routes", "default_route"},
        "expected_inputs": ["input"],
        "expected_outputs": ["selected_route"],
    },
    "final": {
        "allowed_config_keys": {"output_template"},
        "expected_inputs": ["input"],
        "expected_outputs": ["final_output"],
    },
}

_NODE_CONFIG_ALLOWED_KEYS: dict[str, set[str]] = {
    k: v["allowed_config_keys"] for k, v in BUILTIN_NODE_CONTRACTS.items()
}


class WorkflowNode(BaseModel):
    id: str
    type: str
    name: str | None = None
    description: str | None = None
    config: dict = Field(default_factory=dict)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class WorkflowCondition(BaseModel):
    type: str = "always"
    expression: str | None = None
    route_key: str | None = None
    expected_value: str | None = None
    metadata: dict = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str | None = None
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


def _collect_node_dicts(nodes: list) -> list[dict]:
    return [n for n in nodes if isinstance(n, dict)]


class WorkflowValidator:
    @staticmethod
    def validate(config: WorkflowConfig) -> WorkflowValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        node_ids = _collect_node_ids(config.nodes)
        node_dicts = _collect_node_dicts(config.nodes)

        # entrypoint check (skip module paths)
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

        # node type validation
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            if ntype and ntype not in _WORKFLOW_NODE_TYPES:
                errors.append(f"unsupported node type '{ntype}' for node '{nid}'")

        # node config key whitelist
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            node_cfg = node.get("config", {})
            allowed = _NODE_CONFIG_ALLOWED_KEYS.get(ntype)
            if allowed is not None:
                for key in node_cfg:
                    if key not in allowed:
                        warnings.append(f"node '{nid}' (type '{ntype}'): unrecognized config key '{key}'")

        # node type-specific validation + contract validation
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            node_cfg = node.get("config", {})

            if ntype == "rag":
                mode = node_cfg.get("retrieval_mode")
                if mode and mode not in _RAG_RETRIEVAL_MODES:
                    warnings.append(f"node '{nid}': rag retrieval_mode '{mode}' not in {sorted(_RAG_RETRIEVAL_MODES)}")

            if ntype == "tool":
                tool_name = node_cfg.get("tool_name")
                if tool_name is not None and not isinstance(tool_name, str):
                    warnings.append(f"node '{nid}': tool_name should be a string")

            if ntype == "provider":
                pn = node_cfg.get("provider_name")
                if pn is not None and not isinstance(pn, str):
                    warnings.append(f"node '{nid}': provider_name should be a string")

            if ntype == "decision":
                routes = node_cfg.get("routes", [])
                if isinstance(routes, list):
                    for route in routes:
                        route_to = route if isinstance(route, str) else (route.get("to") if isinstance(route, dict) else None)
                        if route_to and route_to not in node_ids:
                            warnings.append(f"node '{nid}': decision route to '{route_to}' not found in nodes")

        # built-in contract validation (expected inputs/outputs)
        for node in node_dicts:
            contract_warnings = WorkflowValidator.validate_contract(node)
            warnings.extend(contract_warnings)

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
                cond = edge.get("condition", {})
                if cond and cond.get("type") not in _WORKFLOW_CONDITION_TYPES:
                    warnings.append(f"edge '{from_id}'→'{to_id}': unsupported condition type '{cond.get('type')}'")

        # terminal_nodes check
        if config.terminal_nodes:
            for tn in config.terminal_nodes:
                if tn not in node_ids:
                    errors.append(f"terminal_nodes includes unknown node '{tn}'")

        return WorkflowValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    @staticmethod
    def validate_contract(node: dict) -> list[str]:
        """Validate a node against its built-in contract. Returns warnings."""
        warnings: list[str] = []
        nid = node.get("id", "")
        ntype = node.get("type", "")
        contract = BUILTIN_NODE_CONTRACTS.get(ntype)
        if contract is None:
            return warnings
        outputs = node.get("outputs", [])
        for exp_out in contract["expected_outputs"]:
            if exp_out not in outputs:
                warnings.append(f"node '{nid}' (type '{ntype}'): expected output '{exp_out}' not declared")
        return warnings
