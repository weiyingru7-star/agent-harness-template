from fastapi.testclient import TestClient

from app.ai_runtime.structured_output import parse_structured_output
from app.main import app


client = TestClient(app)


def test_mock_llm_smoke() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})

    assert response.status_code == 200
    assert response.json() == {
        "provider": "mock",
        "output": "Mock LLM response for: hello",
        "structured_output": None,
    }


def test_mock_llm_structured_smoke() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "structured": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["structured_output"] == {
        "ok": True,
        "provider": "mock",
        "echo": "hello",
    }


def test_unconfigured_openai_compatible_smoke_returns_400() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "openai_compatible"},
    )

    assert response.status_code == 400
    assert "not configured" in response.json()["detail"]


def test_unknown_provider_smoke_returns_400() -> None:
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "unknown"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported LLM provider: unknown"


def test_parse_structured_output_rejects_non_json() -> None:
    assert parse_structured_output("not json") is None
