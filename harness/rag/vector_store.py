from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    id: str
    vector: list[float]
    document_id: str
    chunk_id: str
    collection: str = "default"
    text: str
    metadata: dict = Field(default_factory=dict)


class VectorSearchRequest(BaseModel):
    query_vector: list[float]
    collection: str | None = None
    top_k: int = 10
    metadata_filter: dict | None = None


class VectorSearchResult(BaseModel):
    id: str
    document_id: str
    chunk_id: str
    collection: str
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]: ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None: ...

    @abstractmethod
    def delete_by_collection(self, collection: str) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}
        self._collection_index: dict[str, set[str]] = defaultdict(set)

    def upsert(self, records: list[VectorRecord]) -> None:
        for r in records:
            self._records[r.id] = r
            self._collection_index[r.collection].add(r.id)

    def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        candidates = list(self._records.values())
        if request.collection:
            ids = self._collection_index.get(request.collection, set())
            candidates = [self._records[i] for i in ids if i in self._records]

        scored: list[tuple[float, VectorRecord]] = [
            (self._dot_product(request.query_vector, r.vector), r)
            for r in candidates
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            VectorSearchResult(
                id=r.id,
                document_id=r.document_id,
                chunk_id=r.chunk_id,
                collection=r.collection,
                text=r.text,
                score=score,
                metadata=r.metadata,
            )
            for score, r in scored[: request.top_k]
        ]

    def delete(self, ids: list[str]) -> None:
        for i in ids:
            if i in self._records:
                coll = self._records[i].collection
                self._collection_index[coll].discard(i)
                del self._records[i]

    def delete_by_collection(self, collection: str) -> None:
        ids = self._collection_index.pop(collection, set())
        for i in ids:
            self._records.pop(i, None)

    def count(self) -> int:
        return len(self._records)

    @staticmethod
    def _dot_product(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))
