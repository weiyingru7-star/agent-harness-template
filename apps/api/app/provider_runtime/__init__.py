"""Canonical provider abstraction layer.

New provider features should be added here, not in app.ai_runtime.
See docs/provider-runtime-consolidation.md.
"""

from app.provider_runtime.contracts import ProviderConfig, ProviderError, ProviderRequest, ProviderResponse
from app.provider_runtime.router import call_provider, call_provider_with_fallback

__all__ = [
    "ProviderConfig",
    "ProviderError",
    "ProviderRequest",
    "ProviderResponse",
    "call_provider",
    "call_provider_with_fallback",
]
