import json
from pathlib import Path

from app.registries.agent_template import AgentTemplate, AgentTemplateRegistry


def test_agent_template_creation() -> None:
    t = AgentTemplate(id="test_agent", name="Test Agent")
    assert t.id == "test_agent"
    assert t.name == "Test Agent"
    assert t.provider == "mock"
    assert t.tools == []
    assert t.workflow == "default"
    assert t.eval_cases == []


def test_agent_template_required_fields() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentTemplate(name="no_id")


def test_agent_template_schema_valid(tmp_path: Path) -> None:
    schema_path = Path(__file__).resolve().parents[3] / "schemas" / "agent-template.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "required" in schema
    assert "id" in schema["required"]
    assert "name" in schema["required"]
    assert "properties" in schema


def test_loader_list_templates() -> None:
    loader = AgentTemplateRegistry()
    templates = loader.list_templates()
    assert len(templates) >= 1
    ids = [t.id for t in templates]
    assert "generic_agent" in ids


def test_loader_get_template() -> None:
    loader = AgentTemplateRegistry()
    t = loader.get_template("generic_agent")
    assert t is not None
    assert t.id == "generic_agent"
    assert t.provider == "mock"
    assert "mock_echo" in t.tools


def test_loader_get_missing() -> None:
    loader = AgentTemplateRegistry()
    assert loader.get_template("nonexistent_template") is None


def test_loader_validate_good_json() -> None:
    content = '{"id": "valid", "name": "Valid Agent"}'
    errors = AgentTemplateRegistry.validate_json(content)
    assert errors == []


def test_loader_validate_bad_json() -> None:
    content = '{"name": "missing_id"}'
    errors = AgentTemplateRegistry.validate_json(content)
    assert len(errors) >= 1


def test_loader_validate_invalid_json_syntax() -> None:
    content = "{bad json"
    errors = AgentTemplateRegistry.validate_json(content)
    assert any("JSON parse error" in e for e in errors)


def test_api_list_templates() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [t["id"] for t in data]
    assert "generic_agent" in ids


def test_api_get_template() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/generic_agent")
    assert response.status_code == 200
    t = response.json()
    assert t["id"] == "generic_agent"
    assert t["provider"] == "mock"


def test_api_get_missing_returns_404() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/unknown_template")
    assert response.status_code == 404


def test_template_fields_no_business_terms() -> None:
    t = AgentTemplate(id="neutral", name="Neutral Agent", description="Generic template")
    for field_value in [t.id, t.name, t.description]:
        for term in ["电商", "客服", "服装", "CAD", "商品", "订单", "售后", "自媒体", "竞品", "灯具", "报价"]:
            assert term not in (field_value or "")
