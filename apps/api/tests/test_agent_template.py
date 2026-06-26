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


def test_agent_config_creation() -> None:
    from app.registries.agent_config import AgentConfig, ProviderRef, ToolsConfig, RagConfig

    cfg = AgentConfig(id="test", name="Test")
    assert isinstance(cfg.provider, str)
    assert cfg.provider == "mock"
    assert isinstance(cfg.tools, list)
    assert cfg.rag.enabled is False
    assert cfg.workflow.entrypoint is None


def test_agent_config_shorthand_provider() -> None:
    from app.registries.agent_config import AgentConfig, ProviderRef

    cfg = AgentConfig(id="t1", name="T1", provider="openai_compatible")
    assert cfg.provider == "openai_compatible"


def test_agent_config_nested_provider() -> None:
    from app.registries.agent_config import AgentConfig, ProviderRef

    cfg = AgentConfig(id="t2", name="T2", provider={"provider_name": "openai_compatible", "model": "gpt-4"})
    assert isinstance(cfg.provider, ProviderRef)
    assert cfg.provider.provider_name == "openai_compatible"
    assert cfg.provider.model == "gpt-4"


def test_agent_config_shorthand_tools() -> None:
    from app.registries.agent_config import AgentConfig, ToolsConfig

    cfg = AgentConfig(id="t3", name="T3", tools=["mock_echo", "mock_tool"])
    assert isinstance(cfg.tools, list)
    assert "mock_echo" in cfg.tools


def test_agent_config_nested_tools() -> None:
    from app.registries.agent_config import AgentConfig, ToolsConfig

    cfg = AgentConfig(id="t4", name="T4", tools={"allowed_tools": ["mock_echo"], "required_tools": ["mock_echo"]})
    assert isinstance(cfg.tools, ToolsConfig)
    assert "mock_echo" in cfg.tools.allowed_tools
    assert "mock_echo" in cfg.tools.required_tools


def test_loader_get_config() -> None:
    from app.registries.agent_template import AgentTemplateRegistry

    loader = AgentTemplateRegistry()
    config = loader.get_config("generic_agent")
    assert config is not None
    assert config.id == "generic_agent"


def test_loader_validate_existing() -> None:
    from app.registries.agent_template import AgentTemplateRegistry

    loader = AgentTemplateRegistry()
    errors = loader.validate_template("generic_agent")
    assert errors == []


def test_loader_validate_missing() -> None:
    from app.registries.agent_template import AgentTemplateRegistry

    loader = AgentTemplateRegistry()
    errors = loader.validate_template("nonexistent")
    assert len(errors) >= 1


def test_api_get_config() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/generic_agent/config")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "generic_agent"
    assert "provider" in data
    assert "tools" in data
    assert "rag" in data
    assert "workflow" in data
    assert "eval" in data


def test_api_get_config_missing() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/unknown/config")
    assert response.status_code == 404


def test_api_validate_existing() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/generic_agent/validate")
    assert response.status_code == 200
    assert response.json() == []


def test_v060_template_still_loads() -> None:
    """AgentTemplate with flat fields (V0.6.0 style) still works."""
    from app.registries.agent_template import AgentTemplate

    t = AgentTemplate(id="legacy", name="Legacy", provider="mock", tools=["mock_echo"])
    assert t.provider == "mock"
    assert t.tools == ["mock_echo"]
