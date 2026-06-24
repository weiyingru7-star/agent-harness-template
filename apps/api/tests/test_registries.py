from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_modules() -> None:
    response = client.get("/api/modules")

    assert response.status_code == 200
    modules = response.json()
    assert modules == [
        {
            "id": "demo_agent",
            "name": "Demo Agent",
            "description": "Minimal demo module that runs local mock skill and tool calls.",
        }
    ]


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
