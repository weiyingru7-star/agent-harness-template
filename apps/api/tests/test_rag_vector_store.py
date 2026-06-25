import pytest

from harness.rag.embeddings import EmbeddingRequest, MockEmbeddingProvider
from harness.rag.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
    VectorSearchRequest,
    VectorSearchResult,
)


def test_vector_record_creation() -> None:
    record = VectorRecord(
        id="rec_1", vector=[0.1, 0.2], document_id="doc_1",
        chunk_id="chunk_1", collection="test", text="hello",
    )
    assert record.id == "rec_1"
    assert record.collection == "test"


def test_upsert_and_search() -> None:
    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord(id="r1", vector=[1.0, 0.0], document_id="d1",
                     chunk_id="c1", collection="default", text="a"),
    ])
    results = store.search(VectorSearchRequest(query_vector=[1.0, 0.0], top_k=5))
    assert len(results) == 1
    assert results[0].id == "r1"


def test_search_empty_store() -> None:
    store = InMemoryVectorStore()
    results = store.search(VectorSearchRequest(query_vector=[1.0, 0.0]))
    assert results == []


def test_search_with_collection_filter() -> None:
    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord(id="r1", vector=[1.0, 0.0], document_id="d1",
                     chunk_id="c1", collection="a", text="x"),
        VectorRecord(id="r2", vector=[0.0, 1.0], document_id="d1",
                     chunk_id="c2", collection="b", text="y"),
    ])
    results = store.search(VectorSearchRequest(
        query_vector=[1.0, 0.0], collection="a", top_k=5,
    ))
    assert len(results) == 1
    assert results[0].id == "r1"


def test_search_returns_sorted_by_score() -> None:
    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord(id="near", vector=[0.9, 0.1], document_id="d1",
                     chunk_id="c1", collection="default", text="near"),
        VectorRecord(id="far", vector=[0.1, 0.9], document_id="d1",
                     chunk_id="c2", collection="default", text="far"),
    ])
    results = store.search(VectorSearchRequest(
        query_vector=[1.0, 0.0], top_k=5,
    ))
    assert len(results) == 2
    assert results[0].id == "near"
    assert results[1].id == "far"
    assert results[0].score > results[1].score


def test_delete_by_id() -> None:
    store = InMemoryVectorStore()
    store.upsert([VectorRecord(id="r1", vector=[1.0], document_id="d1",
                               chunk_id="c1", collection="x", text="t")])
    assert store.count() == 1
    store.delete(["r1"])
    assert store.count() == 0


def test_delete_by_collection() -> None:
    store = InMemoryVectorStore()
    store.upsert([VectorRecord(id="r1", vector=[1.0], document_id="d1",
                               chunk_id="c1", collection="x", text="t")])
    store.delete_by_collection("x")
    assert store.count() == 0


def test_cosine_similarity_identical() -> None:
    store = InMemoryVectorStore()
    v = [0.6, 0.8]
    store.upsert([VectorRecord(id="r1", vector=v, document_id="d1",
                               chunk_id="c1", collection="x", text="t")])
    results = store.search(VectorSearchRequest(query_vector=v, top_k=5))
    assert results[0].score == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal() -> None:
    store = InMemoryVectorStore()
    store.upsert([VectorRecord(id="r1", vector=[1.0, 0.0], document_id="d1",
                               chunk_id="c1", collection="x", text="t")])
    results = store.search(VectorSearchRequest(query_vector=[0.0, 1.0], top_k=5))
    assert results[0].score == pytest.approx(0.0, abs=1e-6)


def test_upsert_replaces_existing() -> None:
    store = InMemoryVectorStore()
    store.upsert([VectorRecord(id="r1", vector=[1.0], document_id="d1",
                               chunk_id="c1", collection="x", text="old")])
    store.upsert([VectorRecord(id="r1", vector=[1.0], document_id="d1",
                               chunk_id="c1", collection="x", text="new")])
    results = store.search(VectorSearchRequest(query_vector=[1.0], top_k=5))
    assert results[0].text == "new"


def test_with_mock_embedding_provider() -> None:
    provider = MockEmbeddingProvider()
    emb = provider.embed(EmbeddingRequest(input="hello world"))
    vector = emb.embeddings[0]
    assert len(vector) == 8

    store = InMemoryVectorStore()
    store.upsert([
        VectorRecord(id="r1", vector=vector, document_id="d1",
                     chunk_id="c1", collection="default", text="hello world"),
    ])
    results = store.search(VectorSearchRequest(query_vector=vector, top_k=5))
    assert len(results) == 1
    assert results[0].score > 0.9


def test_large_batch_search() -> None:
    store = InMemoryVectorStore()
    records = [
        VectorRecord(id=f"r{i}", vector=[float(i) / 100, 0.0],
                     document_id="d1", chunk_id=f"c{i}",
                     collection="default", text=str(i))
        for i in range(50)
    ]
    store.upsert(records)
    results = store.search(VectorSearchRequest(query_vector=[0.5, 0.0], top_k=5))
    assert len(results) == 5
    assert all(r.score > 0 for r in results)
