from app.registries.tool_args import ToolArgsValidator
from app.registries.tools import MOCK_ECHO_ARGS_SCHEMA, list_tools


def test_validator_passes_when_schema_is_none() -> None:
    result = ToolArgsValidator.validate({"any": "thing"}, None)

    assert result.valid
    assert result.error is None


def test_validator_passes_valid_args() -> None:
    result = ToolArgsValidator.validate({"input": "hello"}, MOCK_ECHO_ARGS_SCHEMA)

    assert result.valid
    assert result.error is None


def test_validator_fails_missing_required() -> None:
    result = ToolArgsValidator.validate({}, MOCK_ECHO_ARGS_SCHEMA)

    assert not result.valid
    assert result.error is not None
    assert any("missing_required" in detail for detail in result.details)


def test_validator_fails_wrong_type() -> None:
    result = ToolArgsValidator.validate({"input": 123}, MOCK_ECHO_ARGS_SCHEMA)

    assert not result.valid
    assert any("wrong_type" in detail for detail in result.details)


def test_validator_enforces_enum() -> None:
    schema = {
        "type": "object",
        "required": ["mode"],
        "properties": {"mode": {"type": "string", "enum": ["fast", "slow"]}},
    }

    valid_result = ToolArgsValidator.validate({"mode": "fast"}, schema)
    invalid_result = ToolArgsValidator.validate({"mode": "unknown"}, schema)

    assert valid_result.valid
    assert not invalid_result.valid
    assert any("not_in_enum" in detail for detail in invalid_result.details)


def test_validator_blocks_additional_properties() -> None:
    schema = {
        "type": "object",
        "required": ["input"],
        "properties": {"input": {"type": "string"}},
        "additionalProperties": False,
    }

    result = ToolArgsValidator.validate({"input": "x", "extra": 1}, schema)

    assert not result.valid
    assert any("additional_property_forbidden" in detail for detail in result.details)


def test_validator_fails_when_args_not_object() -> None:
    result = ToolArgsValidator.validate("not a dict", MOCK_ECHO_ARGS_SCHEMA)

    assert not result.valid
    assert result.error is not None
    assert result.error.code == "args_not_object"


def test_mock_echo_tool_definition_has_args_schema() -> None:
    tools = list_tools()
    mock_echo = next(tool for tool in tools if tool.id == "mock_echo")

    assert mock_echo.args_schema is not None
    assert mock_echo.args_schema["type"] == "object"
    assert "input" in mock_echo.args_schema["required"]
