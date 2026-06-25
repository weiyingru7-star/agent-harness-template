from app.ai_runtime.providers import MockLLMProvider, OpenAICompatibleProvider
from app.ai_runtime.router import ProviderRouter
from app.core.config import Settings


def test_provider_router_defaults_to_mock() -> None:
    settings = Settings(ai_provider="mock")

    provider = ProviderRouter(settings).resolve()

    assert isinstance(provider, MockLLMProvider)


def test_provider_router_request_overrides_environment_default() -> None:
    settings = Settings(ai_provider="openai_compatible")

    provider = ProviderRouter(settings).resolve("mock")

    assert isinstance(provider, MockLLMProvider)


def test_provider_router_builds_openai_compatible_provider() -> None:
    settings = Settings(
        ai_provider="mock",
        ai_base_url="https://example.invalid/v1",
        ai_api_key="test-key",
        ai_model="test-model",
        ai_timeout=7,
    )

    provider = ProviderRouter(settings).resolve("openai_compatible")

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.base_url == "https://example.invalid/v1"
    assert provider.api_key == "test-key"
    assert provider.model == "test-model"
    assert provider.timeout == 7


def test_provider_router_rejects_unknown_provider() -> None:
    settings = Settings()

    try:
        ProviderRouter(settings).resolve("unknown")
    except ValueError as exc:
        assert str(exc) == "Unsupported LLM provider: unknown"
    else:
        raise AssertionError("expected unknown provider to fail")
