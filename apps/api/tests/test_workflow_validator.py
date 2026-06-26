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
    config = WorkflowConfig(entrypoint="start", nodes=["start", "end"], edges=[["start", "end"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is True


def test_entrypoint_missing_fails() -> None:
    config = WorkflowConfig(entrypoint="missing", nodes=["start", "end"], edges=[["start", "end"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("entrypoint" in e and "missing" in e for e in result.errors)


def test_node_id_duplicate_fails() -> None:
    config = WorkflowConfig(entrypoint="x", nodes=["x", "x"], edges=[["x", "y"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("duplicate" in e for e in result.errors)


def test_edge_unknown_node_fails() -> None:
    config = WorkflowConfig(entrypoint="a", nodes=["a"], edges=[["a", "b"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("unknown" in e and "'b'" in e for e in result.errors)


def test_self_loop_edge_fails() -> None:
    config = WorkflowConfig(entrypoint="a", nodes=["a"], edges=[["a", "a"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("self-loop" in e for e in result.errors)


def test_unsupported_node_type_check() -> None:
    node = WorkflowNode(id="test", type="unsupported_type")
    assert node.type not in {"input", "provider", "tool", "rag", "decision", "final"}


def test_terminal_nodes_unknown_fails() -> None:
    config = WorkflowConfig(entrypoint="a", nodes=["a"], edges=[], terminal_nodes=["unknown"])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert any("terminal_nodes" in e for e in result.errors)


def test_dict_format_nodes_supported() -> None:
    config = WorkflowConfig(entrypoint="start", nodes=["start", "end"], edges=[["start", "end"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is True
    edge = WorkflowEdge(**{"from": "start", "to": "end"})
    assert edge.from_node == "start"


def test_generic_agent_workflow_validates() -> None:
    from app.registries.agent_template import AgentTemplateRegistry

    registry = AgentTemplateRegistry()
    result = registry.validate_template("generic_agent")
    assert result.valid is True


def test_node_with_description_inputs_outputs() -> None:
    n = WorkflowNode(id="n1", type="input", name="Input Node",
                     description="Receives user input",
                     inputs=["raw_text"], outputs=["normalized_text"])
    assert n.description == "Receives user input"
    assert n.inputs == ["raw_text"]


def test_edge_with_id() -> None:
    e = WorkflowEdge(id="e1", **{"from": "a", "to": "b"})
    assert e.id == "e1"
    assert e.from_node == "a"


def test_condition_on_success() -> None:
    c = WorkflowCondition(type="on_success")
    assert c.type == "on_success"


def test_condition_on_failure() -> None:
    c = WorkflowCondition(type="on_failure", expected_value="error")
    assert c.expected_value == "error"


def test_input_node_contract_valid() -> None:
    """input node declaring payload output should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "input", "outputs": ["payload"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_provider_node_contract_valid() -> None:
    """provider node declaring output/usage should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "provider", "outputs": ["output", "usage"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_rag_node_contract_valid() -> None:
    """rag node declaring results/citations should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "rag", "outputs": ["results", "citations"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_tool_node_contract_valid() -> None:
    """tool node declaring result/status should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "tool", "outputs": ["result", "status"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_decision_node_contract_valid() -> None:
    """decision node declaring selected_route should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "decision", "outputs": ["selected_route"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_final_node_contract_valid() -> None:
    """final node declaring final_output should pass contract."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "final", "outputs": ["final_output"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert warnings == []


def test_missing_expected_output_warns() -> None:
    """provider node missing 'usage' output should warn."""
    from app.registries.workflow_validator import WorkflowValidator

    node = {"id": "n1", "type": "provider", "outputs": ["output"]}
    warnings = WorkflowValidator.validate_contract(node)
    assert any("usage" in w for w in warnings)


def test_validation_error_item_creation() -> None:
    from app.registries.workflow_validator import ValidationErrorItem

    item = ValidationErrorItem(code="TEST_CODE", message="test message", path="node.n1", severity="error")
    assert item.code == "TEST_CODE"
    assert item.path == "node.n1"
    assert item.severity == "error"


def test_workflow_result_has_error_items() -> None:
    config = WorkflowConfig(entrypoint="start", nodes=["start", "end"], edges=[["start", "end"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is True
    assert isinstance(result.error_items, list)
    assert len(result.error_items) == 0


def test_invalid_workflow_has_structured_error_items() -> None:
    config = WorkflowConfig(entrypoint="missing", nodes=["a"], edges=[["a", "b"]])
    result = WorkflowValidator.validate(config)
    assert result.valid is False
    assert len(result.error_items) >= 2

    codes = {item.code for item in result.error_items if item.severity == "error"}
    assert "WORKFLOW_ENTRYPOINT_MISSING" in codes
    assert "WORKFLOW_EDGE_TARGET_NOT_FOUND" in codes

    for item in result.error_items:
        assert item.code
        assert item.message
        assert item.severity in ("error", "warning")


def test_error_items_have_path() -> None:
    config = WorkflowConfig(entrypoint="missing", nodes=["x", "x"], edges=[["x", "a"]])
    result = WorkflowValidator.validate(config)
    items_with_path = [i for i in result.error_items if i.path]
    assert items_with_path