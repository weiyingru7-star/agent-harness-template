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


def test_openai_compatible_provider_builds_chat_completion_request(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "hello from provider"}}]}
            ).encode("utf-8")

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(http_request.header_items())
        captured["payload"] = json.loads(http_request.data.decode("utf-8"))
        return FakeResponse()

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

    assert str(exc.value) == "OpenAI-compatible provider request failed"
