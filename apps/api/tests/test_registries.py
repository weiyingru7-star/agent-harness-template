from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_modules() -> None:
    response = client.get("/api/modules")

    assert response.status_code == 200
    modules = response.json()
    demo_agent = next(module for module in modules if module["id"] == "demo_agent")
    assert demo_agent["name"] == "Demo Agent"
    assert demo_agent["version"] == "0.1.0"
    assert demo_agent["description"] == "Generic demo module for local Agent Harness validation."
    assert demo_agent["enabled"] is True
    assert demo_agent["capabilities"] == ["demo", "state_machine"]
    assert demo_agent["default_agent"] == "demo_agent"


def test_list_skills() -> None:
    response = client.get("/api/skills")

    assert response.status_code == 200
    skills = response.json()
    assert skills[0]["id"] == "mock_summarize"


def test_list_tools() -> None:
    response = client.get("/api/tools")

    assert response.status_code == 200
    tools = response.json()
    assert tools[0]["id"] == "mock_echo"
