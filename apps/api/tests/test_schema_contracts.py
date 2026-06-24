import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "schemas"
BUSINESS_TERMS = [
    "电商",
    "客服",
    "服装",
    "CAD",
    "商品",
    "订单",
    "售后",
    "自媒体",
    "竞品",
    "灯具",
    "报价",
]


def test_all_schema_files_are_valid_json_and_have_required_contract_fields() -> None:
    schema_files = sorted(SCHEMA_DIR.glob("*.schema.json"))

    assert schema_files
    for schema_file in schema_files:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        for key in [
            "$schema",
            "title",
            "description",
            "type",
            "required",
            "properties",
            "additionalProperties",
        ]:
            assert key in schema, f"{schema_file.name} missing {key}"
        assert schema["type"] == "object"
        assert isinstance(schema["required"], list)
        assert isinstance(schema["properties"], dict)


def test_schema_property_names_use_snake_case() -> None:
    snake_case = re.compile(r"^[a-z][a-z0-9_]*$")

    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        for property_name in schema["properties"]:
            assert snake_case.fullmatch(property_name), (
                f"{schema_file.name} property is not snake_case: {property_name}"
            )


def test_schema_contracts_are_business_neutral() -> None:
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        content = schema_file.read_text(encoding="utf-8")
        for term in BUSINESS_TERMS:
            assert term not in content, f"{schema_file.name} contains business term: {term}"
