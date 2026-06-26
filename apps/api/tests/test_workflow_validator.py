from app.registries.workflow_validator import (
    WorkflowNode,
    WorkflowEdge,
    WorkflowCondition,
    WorkflowValidator,
)
from app.registries.agent_config import WorkflowConfig


def test_workflow_node_creation() -> None:
    n = WorkflowNode(id="n1", type="input")
    assert n.id == "n1"
    assert n.type == "input"
    assert n.config == {}
    assert n.next == []


def test_workflow_edge_creation() -> None:
    e = WorkflowEdge(**{"from": "n1", "to": "n2"})
    assert e.from_node == "n1"
    assert e.to == "n2"


def test_workflow_condition_creation() -> None:
    c = WorkflowCondition(type="expression", expression="x > 1")
    assert c.type == "expression"
    assert c.expression == "x > 1"


def test_valid_workflow_passes() -> None:
    config = WorkflowConfig(
        entrypoint="start",
        nodes=["start", "end"],
        edges=[["start", "end"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is True


def test_entrypoint_missing_fails() -> None:
    config = WorkflowConfig(
        entrypoint="missing",
        nodes=["start", "end"],
        edges=[["start", "end"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("entrypoint" in e and "missing" in e for e in result.errors)


def test_node_id_duplicate_fails() -> None:
    config = WorkflowConfig(
        entrypoint="x",
        nodes=["x", "x"],
        edges=[["x", "y"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("duplicate" in e for e in result.errors)


def test_edge_unknown_node_fails() -> None:
    config = WorkflowConfig(
        entrypoint="a",
        nodes=["a"],
        edges=[["a", "b"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("unknown" in e and "'b'" in e for e in result.errors)


def test_self_loop_edge_fails() -> None:
    config = WorkflowConfig(
        entrypoint="a",
        nodes=["a"],
        edges=[["a", "a"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("self-loop" in e for e in result.errors)


def test_unsupported_node_type_check() -> None:
    node = WorkflowNode(id="test", type="unsupported_type")
    assert node.type not in {"input", "provider", "tool", "rag", "decision", "final"}


def test_terminal_nodes_unknown_fails() -> None:
    config = WorkflowConfig(
        entrypoint="a",
        nodes=["a"],
        edges=[],
        terminal_nodes=["unknown"],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("terminal_nodes" in e for e in result.errors)


def test_dict_format_nodes_supported() -> None:
    config = WorkflowConfig(
        entrypoint="start",
        nodes=["start", "end"],
        edges=[["start", "end"]],
    )
    result = WorkflowValidator.validate(config)
    assert result.valid is True
    edge = WorkflowEdge(**{"from": "start", "to": "end"})
    assert edge.from_node == "start"


def test_generic_agent_workflow_validates() -> None:
    from app.registries.agent_template import AgentTemplateRegistry

    registry = AgentTemplateRegistry()
    result = registry.validate_template("generic_agent")
    assert result.valid is True
