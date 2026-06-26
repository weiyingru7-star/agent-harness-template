from fastapi.testclient import TestClient

from app.ai_runtime.structured_output import parse_structured_output
from app.main import app


client = TestClient(app)


def test_mock_llm_smoke() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"] == "Mock LLM response for: hello"
    assert data["structured_output"] is None
    assert data["model"] == "mock"
    assert data["latency_ms"] is not None
    assert data["latency_ms"] >= 0
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    assert data["finish_reason"] == "stop"
    assert data["metadata"]["contract"] == "ProviderResponse"
    assert data["metadata"]["provider_runtime_version"] == "v0.5.1"
    assert data["metadata"]["mock"] is True


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
    assert body["model"] == "mock"
    assert body["latency_ms"] is not None
    assert "total_tokens" in body["usage"]
    assert body["finish_reason"] == "stop"
    assert body["metadata"]["mock"] is True


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


def test_smoke_response_has_all_provider_response_fields() -> None:
    response = client.post("/api/llm/smoke", json={"prompt": "contract check"})

    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "output" in data
    assert "structured_output" in data
    assert "model" in data
    assert "latency_ms" in data
    assert "usage" in data
    assert "finish_reason" in data
    assert "metadata" in data
