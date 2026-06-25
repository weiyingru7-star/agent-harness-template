from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = "mock-embedding"
    dimensions: int | None = None
    metadata: dict = Field(default_factory=dict)


class EmbeddingResult(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int
    usage: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...


class _LCG:
    """Linear Congruential Generator for deterministic pseudo-random floats."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0x7FFFFFFF

    def next(self) -> float:
        self._state = (self._state * 1103515245 + 12345) & 0x7FFFFFFF
        return self._state / 0x7FFFFFFF


_MOCK_DIMENSIONS = 8


class MockEmbeddingProvider(EmbeddingProvider):
    provider_name = "mock-embedding"

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        inputs = [request.input] if isinstance(request.input, str) else request.input
        dims = request.dimensions or _MOCK_DIMENSIONS
        embeddings = [self._embed_text(t, dims) for t in inputs]
        return EmbeddingResult(
            embeddings=embeddings,
            model="mock-embedding",
            dimensions=dims,
            usage={"prompt_tokens": sum(len(t.split()) for t in inputs)},
        )

    @staticmethod
    def _embed_text(text: str, dims: int) -> list[float]:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        rng = _LCG(seed)
        raw = [rng.next() for _ in range(dims)]
        norm = sum(x * x for x in raw) ** 0.5
        if norm == 0:
            return [0.0] * dims
        return [x / norm for x in raw]


class EmbeddingRegistry:
    _providers: dict[str, EmbeddingProvider] = {}

    @classmethod
    def register(cls, provider: EmbeddingProvider) -> None:
        cls._providers[provider.provider_name] = provider

    @classmethod
    def get(cls, name: str = "mock-embedding") -> EmbeddingProvider:
        provider = cls._providers.get(name)
        if provider is None:
            msg = f"Unknown embedding provider: {name}"
            raise ValueError(msg)
        return provider

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def reset(cls) -> None:
        cls._providers.clear()
