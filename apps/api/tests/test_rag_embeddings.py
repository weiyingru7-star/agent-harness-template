from harness.rag.embeddings import EmbeddingRegistry, EmbeddingRequest, MockEmbeddingProvider


def test_mock_provider_returns_fixed_dimensions() -> None:
    provider = MockEmbeddingProvider()
    result = provider.embed(EmbeddingRequest(input="hello"))

    assert len(result.embeddings) == 1
    assert result.dimensions == 8
    assert len(result.embeddings[0]) == 8


def test_same_input_same_embedding() -> None:
    provider = MockEmbeddingProvider()
    r1 = provider.embed(EmbeddingRequest(input="hello world"))
    r2 = provider.embed(EmbeddingRequest(input="hello world"))

    assert r1.embeddings[0] == r2.embeddings[0]


def test_different_input_different_embedding() -> None:
    provider = MockEmbeddingProvider()
    r1 = provider.embed(EmbeddingRequest(input="hello"))
    r2 = provider.embed(EmbeddingRequest(input="world"))

    assert r1.embeddings[0] != r2.embeddings[0]


def test_batch_input() -> None:
    provider = MockEmbeddingProvider()
    result = provider.embed(EmbeddingRequest(input=["a", "b", "c"]))

    assert len(result.embeddings) == 3
    assert result.dimensions == 8


def test_custom_dimensions() -> None:
    provider = MockEmbeddingProvider()
    result = provider.embed(EmbeddingRequest(input="test", dimensions=16))

    assert result.dimensions == 16
    assert len(result.embeddings[0]) == 16


def test_registry_get_mock_provider() -> None:
    provider = EmbeddingRegistry.get("mock-embedding")

    assert isinstance(provider, MockEmbeddingProvider)


def test_registry_list_providers() -> None:
    providers = EmbeddingRegistry.list_providers()

    assert "mock-embedding" in providers


def test_registry_unknown_provider_raises() -> None:
    try:
        EmbeddingRegistry.get("unknown_provider")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_embedding_model_name_in_result() -> None:
    provider = MockEmbeddingProvider()
    result = provider.embed(EmbeddingRequest(input="hello"))

    assert result.model == "mock-embedding"


