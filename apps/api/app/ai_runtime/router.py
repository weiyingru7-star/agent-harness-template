from dataclasses import dataclass

from app.ai_runtime.providers import (
    MockFailingLLMProvider,
    MockFlakyLLMProvider,
    MockLLMProvider,
    MockSlowLLMProvider,
    OpenAICompatibleProvider,
)
from app.core.config import Settings


@dataclass(frozen=True)
class ProviderRouter:
    settings: Settings

    def resolve(self, requested_provider: str | None = None):
        provider_id = (requested_provider or self.settings.ai_provider or "mock").strip()
        if provider_id == "mock":
            return MockLLMProvider()
        if provider_id == "mock_failing":
            return MockFailingLLMProvider()
        if provider_id == "mock_slow":
            return MockSlowLLMProvider(delay_ms=3000)
        if provider_id == "mock_flaky":
            return MockFlakyLLMProvider()
        if provider_id == "openai_compatible":
            return OpenAICompatibleProvider(
                base_url=self.settings.ai_base_url,
                api_key=self.settings.ai_api_key,
                model=self.settings.ai_model,
                timeout=self.settings.ai_timeout,
            )

        raise ValueError(f"Unsupported LLM provider: {provider_id}")
