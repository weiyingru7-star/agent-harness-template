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


ERROR_CODES: dict[str, str] = {
    "entrypoint_missing": "WORKFLOW_ENTRYPOINT_MISSING",
    "node_duplicate": "WORKFLOW_NODE_DUPLICATE",
    "edge_target_not_found": "WORKFLOW_EDGE_TARGET_NOT_FOUND",
    "node_type_unsupported": "WORKFLOW_NODE_TYPE_UNSUPPORTED",
    "condition_type_unsupported": "WORKFLOW_CONDITION_TYPE_UNSUPPORTED",
    "self_loop": "WORKFLOW_SELF_LOOP",
    "terminal_node_not_found": "WORKFLOW_TERMINAL_NODE_NOT_FOUND",
    "config_key_unknown": "WORKFLOW_CONFIG_KEY_UNKNOWN",
    "retrieval_mode_invalid": "WORKFLOW_RAG_RETRIEVAL_MODE_INVALID",
    "expected_output_missing": "WORKFLOW_EXPECTED_OUTPUT_MISSING",
    "decision_route_not_found": "WORKFLOW_DECISION_ROUTE_NOT_FOUND",
}


class ValidationErrorItem(BaseModel):
    code: str
    message: str
    path: str | None = None
    severity: str = "error"
    metadata: dict = Field(default_factory=dict)


class WorkflowValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_items: list[ValidationErrorItem] = Field(default_factory=list)


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
        items: list[ValidationErrorItem] = []

        def _err(code: str, msg: str, path: str | None = None) -> None:
            errors.append(msg)
            items.append(ValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path))

        def _warn(code: str, msg: str, path: str | None = None) -> None:
            warnings.append(msg)
            items.append(ValidationErrorItem(
                code=ERROR_CODES.get(code, code), message=msg, path=path, severity="warning"))

        node_ids = _collect_node_ids(config.nodes)
        node_dicts = _collect_node_dicts(config.nodes)

        # entrypoint check (skip module paths)
        if config.entrypoint and "." not in config.entrypoint and ":" not in config.entrypoint:
            if config.entrypoint not in node_ids:
                _err("entrypoint_missing",
                     f"entrypoint '{config.entrypoint}' not found in nodes",
                     path="entrypoint")

        # node id uniqueness
        seen: set[str] = set()
        for node in config.nodes:
            nid = node if isinstance(node, str) else (node.get("id") if isinstance(node, dict) else None)
            if nid and nid in seen:
                _err("node_duplicate", f"duplicate node id '{nid}'", path=f"node.{nid}")
            if nid:
                seen.add(nid)

        # node type validation
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            if ntype and ntype not in _WORKFLOW_NODE_TYPES:
                _err("node_type_unsupported",
                     f"unsupported node type '{ntype}' for node '{nid}'",
                     path=f"node.{nid}")

        # node config key whitelist
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            node_cfg = node.get("config", {})
            allowed = _NODE_CONFIG_ALLOWED_KEYS.get(ntype)
            if allowed is not None:
                for key in node_cfg:
                    if key not in allowed:
                        _warn("config_key_unknown",
                              f"node '{nid}' (type '{ntype}'): unrecognized config key '{key}'",
                              path=f"node.{nid}")

        # node type-specific validation + contract validation
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            node_cfg = node.get("config", {})

            if ntype == "rag":
                mode = node_cfg.get("retrieval_mode")
                if mode and mode not in _RAG_RETRIEVAL_MODES:
                    _warn("retrieval_mode_invalid",
                          f"node '{nid}': rag retrieval_mode '{mode}' not in {sorted(_RAG_RETRIEVAL_MODES)}",
                          path=f"node.{nid}")

            if ntype == "tool":
                tool_name = node_cfg.get("tool_name")
                if tool_name is not None and not isinstance(tool_name, str):
                    _warn("invalid_tool_name",
                          f"node '{nid}': tool_name should be a string",
                          path=f"node.{nid}")

            if ntype == "provider":
                pn = node_cfg.get("provider_name")
                if pn is not None and not isinstance(pn, str):
                    _warn("invalid_provider_name",
                          f"node '{nid}': provider_name should be a string",
                          path=f"node.{nid}")

            if ntype == "decision":
                routes = node_cfg.get("routes", [])
                if isinstance(routes, list):
                    for ri, route in enumerate(routes):
                        route_to = route if isinstance(route, str) else (route.get("to") if isinstance(route, dict) else None)
                        if route_to and route_to not in node_ids:
                            _warn("decision_route_not_found",
                                  f"node '{nid}': decision route to '{route_to}' not found in nodes",
                                  path=f"node.{nid}.routes[{ri}]")

        # built-in contract validation
        for node in node_dicts:
            nid = node.get("id", "")
            ntype = node.get("type", "")
            contract = BUILTIN_NODE_CONTRACTS.get(ntype)
            if contract:
                outputs = node.get("outputs", [])
                for exp_out in contract["expected_outputs"]:
                    if exp_out not in outputs:
                        _warn("expected_output_missing",
                              f"node '{nid}' (type '{ntype}'): expected output '{exp_out}' not declared",
                              path=f"node.{nid}.outputs")

        # edge validation
        for ei, edge in enumerate(config.edges):
            if isinstance(edge, list) and len(edge) >= 2:
                from_id, to_id = edge[0], edge[1]
                if from_id not in node_ids:
                    _err("edge_target_not_found",
                         f"edge references unknown node '{from_id}'",
                         path=f"edge[{ei}].from")
                if to_id not in node_ids:
                    _err("edge_target_not_found",
                         f"edge references unknown node '{to_id}'",
                         path=f"edge[{ei}].to")
                if from_id == to_id:
                    _err("self_loop",
                         f"edge from '{from_id}' to '{to_id}' is a self-loop",
                         path=f"edge[{ei}]")
            elif isinstance(edge, dict):
                from_id = edge.get("from", "")
                to_id = edge.get("to", "")
                if from_id not in node_ids:
                    _err("edge_target_not_found",
                         f"edge references unknown node '{from_id}'",
                         path=f"edge[{ei}].from")
                if to_id not in node_ids:
                    _err("edge_target_not_found",
                         f"edge references unknown node '{to_id}'",
                         path=f"edge[{ei}].to")
                cond = edge.get("condition", {})
                if cond and cond.get("type") not in _WORKFLOW_CONDITION_TYPES:
                    _warn("condition_type_unsupported",
                          f"edge '{from_id}'→'{to_id}': unsupported condition type '{cond.get('type')}'",
                          path=f"edge[{ei}].condition")

        # terminal_nodes check
        if config.terminal_nodes:
            for tn in config.terminal_nodes:
                if tn not in node_ids:
                    _err("terminal_node_not_found",
                         f"terminal_nodes includes unknown node '{tn}'",
                         path="terminal_nodes")

        return WorkflowValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings, error_items=items)

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
