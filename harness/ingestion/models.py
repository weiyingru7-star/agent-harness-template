from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ParsedDoc(BaseModel):
    source_filename: str
    content_type: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None


class ManifestDocument(BaseModel):
    document_id: str
    document_key: str
    document_version: int = 1
    source_hash: str
    source_filename: str
    content_type: str
    status: str = "active"
    cleaned_path: str
    chunk_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManifestChunk(BaseModel):
    document_id: str
    chunk_index: int
    text: str
    char_count: int
    token_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Manifest(BaseModel):
    pipeline_version: str = "v1.5"
    tenant_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    documents: list[ManifestDocument] = Field(default_factory=list)
    chunks: list[ManifestChunk] = Field(default_factory=list)
