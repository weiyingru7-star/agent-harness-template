"""Type-aware chunker — wraps existing harness/rag/chunking.

For txt/md/pdf/docx: use paragraph-based chunking.
For csv/xlsx: preserve row groups.
Uses lazy import to avoid triggering DB init at import time.
"""

from typing import Any

from harness.ingestion.models import ParsedDoc


def chunk_document(
    doc: ParsedDoc,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[dict[str, Any]]:
    """Split a cleaned document into preview chunks.

    These are PREVIEW chunks — final chunking is done by KnowledgeStore.
    Returns a list of dicts with text, char_count, token_count.
    """
    text = doc.text.strip()
    if not text:
        return []

    from harness.rag.chunking import chunk_text_with_strategy
    from harness.rag.chunking_types import ChunkingConfig

    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        split_by="paragraph",
        preserve_paragraphs=True,
    )
    results = chunk_text_with_strategy(text, config)
    return [
        {
            "text": r.text,
            "char_count": r.char_count,
            "token_count": r.token_count,
        }
        for r in results
    ]
