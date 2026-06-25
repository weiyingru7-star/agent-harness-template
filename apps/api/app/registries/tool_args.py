from __future__ import annotations

from dataclasses import dataclass, field


class ToolArgsValidationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


@dataclass
class ArgsValidationResult:
    valid: bool
    error: ToolArgsValidationError | None = None
    details: list[str] = field(default_factory=list)


_ALLOWED_TYPES = {"string", "number", "integer", "boolean", "array", "object", "null"}


class ToolArgsValidator:
    @staticmethod
    def validate(args: object, schema: dict | None) -> ArgsValidationResult:
        if schema is None:
            return ArgsValidationResult(valid=True)

        if not isinstance(args, dict):
            err = ToolArgsValidationError(
                code="args_not_object",
                message=f"tool args must be an object, got {type(args).__name__}",
            )
            return ArgsValidationResult(valid=False, error=err, details=[err.message])

        errors: list[str] = []
        schema_type = schema.get("type")
        if schema_type is not None and schema_type != "object":
            return ArgsValidationResult(
                valid=True,
                details=[f"schema type '{schema_type}' not enforced by minimal validator"],
            )

        required = schema.get("required") or []
        for field_name in required:
            if field_name not in args:
                errors.append(f"missing_required: {field_name}")

        properties = schema.get("properties") or {}
        for field_name, value in args.items():
            if field_name not in properties:
                if schema.get("additionalProperties") is False:
                    errors.append(f"additional_property_forbidden: {field_name}")
                continue
            field_schema = properties[field_name] or {}
            type_errors = ToolArgsValidator._check_type(field_name, value, field_schema)
            errors.extend(type_errors)
            enum_errors = ToolArgsValidator._check_enum(field_name, value, field_schema)
            errors.extend(enum_errors)

        if errors:
            err = ToolArgsValidationError(
                code="validation_failed",
                message="; ".join(errors),
                details=errors,
            )
            return ArgsValidationResult(valid=False, error=err, details=errors)

        return ArgsValidationResult(valid=True)

    @staticmethod
    def _check_type(field_name: str, value: object, field_schema: dict) -> list[str]:
        declared_type = field_schema.get("type")
        if declared_type is None:
            return []
        if declared_type not in _ALLOWED_TYPES:
            return [f"{field_name}: unsupported schema type '{declared_type}'"]
        actual_type = ToolArgsValidator._python_type_name(value)
        if not ToolArgsValidator._type_matches(actual_type, declared_type):
            return [f"wrong_type: {field_name} expected {declared_type}, got {actual_type}"]
        return []

    @staticmethod
    def _check_enum(field_name: str, value: object, field_schema: dict) -> list[str]:
        enum_values = field_schema.get("enum")
        if enum_values is None:
            return []
        if value not in enum_values:
            return [f"not_in_enum: {field_name} value not in allowed values"]
        return []

    @staticmethod
    def _python_type_name(value: object) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        if value is None:
            return "null"
        return type(value).__name__

    @staticmethod
    def _type_matches(actual: str, declared: str) -> bool:
        if actual == declared:
            return True
        if declared == "number" and actual == "integer":
            return True
        return False
