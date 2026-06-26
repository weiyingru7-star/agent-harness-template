import pytest

from app.provider_runtime import (
    call_provider,
    call_provider_with_fallback,
)
from app.provider_runtime.contracts import ProviderRequest, ProviderResponse, ProviderError


def test_provider_request_creation() -> None:
    req = ProviderRequest(input="hello")
    assert req.input == "hello"
    assert req.model == "mock"
    assert req.metadata == {}


def test_provider_response_creation() -> None:
    resp = ProviderResponse(output="hello", model="mock", provider="mock")
    assert resp.output == "hello"
    assert resp.provider == "mock"
    assert resp.latency_ms is None


def test_provider_error_creation() -> None:
    err = ProviderError(
        error_type="ProviderTimeout",
        error_message="timed out",
        provider="test",
    )
    assert err.error_type == "ProviderTimeout"
    assert err.retryable is False
    assert err.model == "unknown"


def test_call_provider_mock() -> None:
    resp = call_provider("hello")
    assert isinstance(resp, ProviderResponse)
    assert resp.output.startswith("Mock LLM response")
    assert resp.provider == "mock"
    assert resp.model == "mock"
    assert resp.latency_ms is not None


def test_call_provider_response_has_metadata() -> None:
    resp = call_provider("hello world")
    assert resp.provider == "mock"
    assert resp.model == "mock"
    assert resp.latency_ms >= 0
    assert "estimated_tokens" in resp.usage


def test_fallback_on_unknown_primary() -> None:
    resp = call_provider_with_fallback("hello", primary="unknown", fallback="mock")
    assert isinstance(resp, ProviderResponse)
    assert resp.provider == "mock"
    assert "fallback_from" in resp.metadata
    assert resp.metadata["fallback_from"] == "unknown"
    assert resp.metadata["fallback_to"] == "mock"
    assert "fallback_reason" in resp.metadata


def test_fallback_metadata() -> None:
    resp = call_provider_with_fallback("test", primary="unknown", fallback="mock")
    assert resp.metadata["fallback_from"] == "unknown"
    assert resp.metadata["fallback_to"] == "mock"
    assert "ValueError" in resp.metadata["fallback_reason"]


def test_latency_ms_is_recorded() -> None:
    resp = call_provider("hello")
    assert resp.latency_ms is not None
    assert resp.latency_ms >= 0


def test_usage_estimated_tokens() -> None:
    resp = call_provider("hello world test prompt")
    assert resp.usage["estimated_tokens"] == 4


def test_existing_llm_smoke_unchanged() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/llm/smoke", json={"prompt": "hello"})
    assert response.status_code == 200
    assert response.json() == {
        "provider": "mock",
        "output": "Mock LLM response for: hello",
        "structured_output": None,
    }


def test_existing_structured_smoke_unchanged() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "structured": True},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert response.json()["structured_output"]["ok"] is True
