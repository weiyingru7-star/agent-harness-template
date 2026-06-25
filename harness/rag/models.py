from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(BaseModel):
    id: str
    file_id: str
    filename: str
    source_type: str = "file"
    collection: str | None = None
    title: str | None = None
    source: str | None = None
    content_type: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Chunk(BaseModel):
    id: str
    document_id: str
    file_id: str
    text: str
    index: int
    collection: str | None = None
    char_count: int = 0
    token_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    file_id: str
    filename: str
    chunk_index: int
    title: str | None = None
    source: str | None = None
    quote: str | None = None
    score: int = 0
    collection: str | None = None


class RetrieveResult(BaseModel):
    chunk: Chunk
    score: int
    citation: Citation


class IngestResponse(BaseModel):
    document: Document
    chunks: list[Chunk]


class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrieveResult]
