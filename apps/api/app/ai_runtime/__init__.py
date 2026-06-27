"""Legacy compatibility layer for LLM providers.

New provider features should be added in app.provider_runtime.
This layer is retained for backward compatibility with routes and tests.
See docs/provider-runtime-consolidation.md.
"""
from app.ai_runtime.client import LLMClient, LLMResponse
from app.ai_runtime.providers import MockLLMProvider, OpenAICompatibleProvider
from app.ai_runtime.router import ProviderRouter
from app.ai_runtime.structured_output import parse_structured_output

__all__ = [
    "LLMClient",
    "LLMResponse",
    "MockLLMProvider",
    "OpenAICompatibleProvider",
    "ProviderRouter",
    "parse_structured_output",
]
