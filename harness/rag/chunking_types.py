from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=500, ge=50, le=4000)
    chunk_overlap: int = Field(default=0, ge=0, le=500)
    split_by: str = Field(default="paragraph")
    preserve_paragraphs: bool = True
    min_chunk_size: int = Field(default=50, ge=10)


@dataclass
class ChunkResult:
    text: str
    chunk_index: int
    char_count: int
    token_count: int
    start_char: int
    end_char: int
    split_strategy: str
    overlap_with_previous: int = 0
