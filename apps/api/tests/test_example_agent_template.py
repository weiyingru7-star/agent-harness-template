from app.registries.agent_template import AgentTemplateRegistry
from app.registries.agent_config import AgentConfig


def test_example_is_loadable() -> None:
    loader = AgentTemplateRegistry()
    config = loader.get_config("generic_agent")
    assert config is not None
    assert isinstance(config, AgentConfig)


def test_example_api_list() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert "generic_agent" in ids


def test_example_api_get() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/generic_agent")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "generic_agent"


def test_example_api_config() -> None:
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


def test_example_api_validate() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/agent-templates/generic_agent/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_example_description_is_business_neutral() -> None:
    loader = AgentTemplateRegistry()
    config = loader.get_config("generic_agent")
    assert config is not None
    text = f"{config.id} {config.name} {config.description}"
    for term in ["电商", "客服", "服装", "CAD", "商品", "订单", "售后", "自媒体", "竞品", "灯具", "报价"]:
        assert term not in text


def test_example_metadata_is_business_neutral() -> None:
    loader = AgentTemplateRegistry()
    config = loader.get_config("generic_agent")
    assert config is not None
    meta_text = str(config.metadata)
    for term in ["电商", "客服", "服装", "CAD", "商品", "订单", "售后", "自媒体", "竞品", "灯具", "报价"]:
        assert term not in meta_text


def test_example_template_readme_exists() -> None:
    from pathlib import Path

    readme = Path(__file__).resolve().parents[3] / "templates" / "agent-template" / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "generic_agent" in content
