from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(BaseModel):
    id: str
    file_id: str
    filename: str
    source_type: str = "file"
    created_at: datetime = Field(default_factory=utc_now)


class Chunk(BaseModel):
    id: str
    document_id: str
    file_id: str
    text: str
    index: int
    created_at: datetime = Field(default_factory=utc_now)


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    file_id: str
    filename: str
    chunk_index: int


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
