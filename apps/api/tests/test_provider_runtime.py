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
    data = response.json()
    assert data["provider"] == "mock"
    assert data["output"] == "Mock LLM response for: hello"
    assert data["structured_output"] is None
    assert data["model"] == "mock"
    assert data["latency_ms"] is not None
    assert "prompt_tokens" in data["usage"]
    assert data["finish_reason"] == "stop"
    assert data["metadata"]["contract"] == "ProviderResponse"


def test_existing_structured_smoke_unchanged() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "structured": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["structured_output"]["ok"] is True
    assert data["model"] == "mock"
    assert data["latency_ms"] is not None
    assert "completion_tokens" in data["usage"]
    assert data["finish_reason"] == "stop"


def test_mock_provider_stream_text_yields_words() -> None:
    from app.ai_runtime.providers import MockLLMProvider

    provider = MockLLMProvider()
    deltas = list(provider.stream_text("hello world"))
    assert len(deltas) >= 1
    combined = "".join(deltas)
    assert combined == "Mock LLM response for: hello world"


def test_generate_stream_events_order() -> None:
    from app.ai_runtime.client import LLMClient
    from app.ai_runtime.providers import MockLLMProvider

    provider = MockLLMProvider()
    client = LLMClient(provider)
    events = list(client.generate_stream("hello"))

    assert events[0].event_type == "stream_start"
    assert any(e.event_type == "stream_delta" for e in events)
    assert events[-1].event_type == "stream_end"


def test_generate_stream_index_continuous() -> None:
    from app.ai_runtime.client import LLMClient
    from app.ai_runtime.providers import MockLLMProvider

    provider = MockLLMProvider()
    client = LLMClient(provider)
    events = list(client.generate_stream("hello"))

    for i, event in enumerate(events):
        assert event.index == i


def test_mock_failing_provider_raises() -> None:
    from app.ai_runtime.providers import MockFailingLLMProvider, ProviderRequestError

    provider = MockFailingLLMProvider()
    with pytest.raises(ProviderRequestError):
        provider.generate("hello")


def test_provider_error_fields() -> None:
    err = ProviderError(
        error_type="ProviderExecutionError",
        error_message="something broke",
        provider="mock_failing",
        model="mock",
        retryable=True,
    )
    assert err.error_type == "ProviderExecutionError"
    assert err.retryable is True
    assert err.model == "mock"


def test_smoke_fallback_unknown_primary() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "unknown", "fallback": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert data["output"].startswith("Mock LLM response")
    assert data["metadata"]["fallback_used"] is True
    assert data["metadata"]["fallback_from"] == "unknown"
    assert data["metadata"]["primary_error_type"] == "ValueError"


def test_fallback_metadata_has_all_fields() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/llm/smoke",
        json={"prompt": "hello", "provider": "mock_failing", "fallback": "mock"},
    )
    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert meta["fallback_used"] is True
    assert meta["fallback_from"] == "mock_failing"
    assert meta["fallback_to"] == "mock"
    assert "fallback_reason" in meta
    assert meta["primary_error_type"] == "ProviderRequestError"
    assert "fallback_used" in meta


def test_mock_slow_provider_returns_normally_without_timeout() -> None:
    from app.ai_runtime.providers import MockSlowLLMProvider

    provider = MockSlowLLMProvider(delay_ms=1)
    result = provider.generate("hello")
    assert result.output.startswith("Mock LLM slow response")


def test_mock_slow_provider_times_out() -> None:
    from app.ai_runtime.providers import MockSlowLLMProvider, ProviderTimeoutError
    from app.provider_runtime.router import _run_with_timeout

    provider = MockSlowLLMProvider(delay_ms=500)
    with pytest.raises(ProviderTimeoutError):
        _run_with_timeout(provider.generate, ("hello",), timeout_ms=50)


def test_mock_flaky_provider_fails_first_then_succeeds() -> None:
    from app.provider_runtime.router import call_provider_with_timeout_retry

    response = call_provider_with_timeout_retry(
        "hello", provider_name="mock_flaky", max_attempts=2,
    )
    assert response.output.startswith("Mock LLM flaky response")


def test_retry_metadata_includes_attempts() -> None:
    from app.provider_runtime.router import call_provider_with_timeout_retry

    response = call_provider_with_timeout_retry(
        "hello", provider_name="mock_flaky", max_attempts=2,
    )
    meta = response.metadata
    assert meta["retried"] is True
    assert meta["retry_count"] == 1
    assert meta["max_attempts"] == 2
    assert meta["final_attempt_status"] == "completed"
    assert len(meta["attempts"]) == 2
    assert meta["attempts"][0]["status"] == "failed"
    assert meta["attempts"][0]["error_type"] == "ProviderRequestError"
    assert meta["attempts"][1]["status"] == "completed"


def test_no_retry_on_non_retryable_error() -> None:
    from app.provider_runtime.router import call_provider_with_timeout_retry

    with pytest.raises(ValueError):
        call_provider_with_timeout_retry(
            "hello", provider_name="unknown", max_attempts=2,
        )


def test_call_provider_timeout_ms_sets_usage() -> None:
    from app.provider_runtime.router import call_provider_with_timeout_retry

    response = call_provider_with_timeout_retry("hello", provider_name="mock")
    assert "prompt_tokens" in response.usage
    assert response.usage["prompt_tokens"] == 1


def test_provider_config_defaults() -> None:
    from app.provider_runtime.contracts import ProviderConfig

    cfg = ProviderConfig()
    assert cfg.provider_name == "mock"
    assert cfg.api_key_configured is False
    assert cfg.model == ""
    assert cfg.max_attempts == 1
    assert cfg.fallback_provider == "mock"
    assert cfg.streaming_enabled is True


def test_provider_config_no_key_exposed() -> None:
    from app.provider_runtime.contracts import ProviderConfig

    cfg = ProviderConfig(api_key_configured=True)
    assert cfg.api_key_configured is True
    assert not hasattr(cfg, "api_key")
