import json
from urllib import error

import pytest

from app.ai_runtime.providers import (
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderRequestError,
)


def test_openai_compatible_provider_requires_configuration() -> None:
    provider = OpenAICompatibleProvider(base_url="", api_key="", model="")

    with pytest.raises(ProviderConfigurationError) as exc:
        provider.generate_text("hello")

    message = str(exc.value)
    assert "base_url" in message
    assert "api_key" in message
    assert "model" in message


def _mock_openai_response(content: str = "hello from provider") -> json:
    return json.dumps({
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "model": "test-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15,
        },
    }).encode("utf-8")


class _FakeOpenAIResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return _mock_openai_response()


def test_openai_compatible_provider_builds_chat_completion_request(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(http_request.header_items())
        captured["payload"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeOpenAIResponse()

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1/",
        api_key="test-key",
        model="test-model",
        timeout=3,
    )

    result = provider.generate_json("return json")

    assert result.output == "hello from provider"
    assert captured["url"] == "https://example.invalid/v1/chat/completions"
    assert captured["timeout"] == 3
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"] == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "return json"}],
        "response_format": {"type": "json_object"},
    }


def test_openai_compatible_provider_wraps_network_errors(monkeypatch) -> None:
    def fake_urlopen(http_request, timeout):
        raise error.URLError("offline")

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )

    with pytest.raises(ProviderRequestError) as exc:
        provider.generate_text("hello")

    assert "network error" in str(exc.value)


def test_openai_provider_extracts_usage_from_response(monkeypatch) -> None:
    def fake_urlopen(http_request, timeout):
        return _FakeOpenAIResponse()

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )

    result = provider.generate_text("hello")
    meta = result.metadata or {}

    assert meta["usage"]["prompt_tokens"] == 5
    assert meta["usage"]["completion_tokens"] == 10
    assert meta["usage"]["total_tokens"] == 15


def test_openai_provider_extracts_finish_reason(monkeypatch) -> None:
    def fake_urlopen(http_request, timeout):
        return _FakeOpenAIResponse()

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )

    result = provider.generate_text("hello")
    meta = result.metadata or {}

    assert meta["finish_reason"] == "stop"


def test_openai_provider_extracts_model_from_response(monkeypatch) -> None:
    def fake_urlopen(http_request, timeout):
        return _FakeOpenAIResponse()

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )

    result = provider.generate_text("hello")
    meta = result.metadata or {}

    assert meta["model"] == "test-model"


def test_openai_provider_http_error_parses_body(monkeypatch) -> None:
    error_body = json.dumps({
        "error": {"message": "Incorrect API key provided", "type": "authentication_error"}
    }).encode("utf-8")

    def fake_urlopen(http_request, timeout):
        raise error.HTTPError(
            url="https://example.invalid/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None,
        )

    monkeypatch.setattr("app.ai_runtime.providers.request.urlopen", fake_urlopen)
    monkeypatch.setattr(
        "app.ai_runtime.providers.error.HTTPError.read",
        lambda self: error_body,
        raising=False,
    )

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        api_key="bad-key",
        model="test-model",
    )

    with pytest.raises(ProviderRequestError) as exc:
        provider.generate_text("hello")

    assert "401" in str(exc.value)
    assert "Incorrect API key" in str(exc.value)
