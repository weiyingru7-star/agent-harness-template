from __future__ import annotations

from harness.rag.chunking_types import ChunkResult, ChunkingConfig


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Original chunking — kept for backward compatibility."""
    normalized = text.strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
        elif len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def chunk_text_with_strategy(text: str, config: ChunkingConfig) -> list[ChunkResult]:
    """Chunk text with full strategy support.

    Algorithm (split_by=paragraph, the default):
      1. Split by \\n\\n into paragraphs.
      2. Merge paragraphs into chunks up to chunk_size.
      3. Paragraphs exceeding chunk_size × 1.2 fall back to fixed_chars splitting.
      4. If chunk_overlap > 0, apply as a post-process.
    """
    normalized = text.strip()
    if not normalized:
        return []

    if config.split_by == "fixed_chars":
        raw = _fixed_chars_split(normalized, config)
        return _apply_overlap(raw, config.chunk_overlap)

    # --- paragraph-first ---
    raw_paragraphs = normalized.split("\n\n")
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    intermediate: list[tuple[str, str]] = []  # (text, strategy)
    buffer = ""
    buffer_strategy = "paragraph"

    for para in paragraphs:
        para_len = len(para)

        if not buffer:
            if para_len > int(config.chunk_size * 1.2):
                _flush_paragraph_buffer(intermediate, buffer, buffer_strategy)
                buffer = ""
                for chunk in _fixed_chars_split(para, config):
                    intermediate.append((chunk.text, "fixed_chars"))
            else:
                buffer = para
        else:
            would_be = len(buffer) + 2 + para_len
            if para_len > int(config.chunk_size * 1.2):
                _flush_paragraph_buffer(intermediate, buffer, buffer_strategy)
                for chunk in _fixed_chars_split(para, config):
                    intermediate.append((chunk.text, "fixed_chars"))
                buffer = ""
            elif would_be <= config.chunk_size:
                buffer = f"{buffer}\n\n{para}"
            else:
                _flush_paragraph_buffer(intermediate, buffer, buffer_strategy)
                buffer = para

    _flush_paragraph_buffer(intermediate, buffer, buffer_strategy)

    raw_results = _intermediate_to_results(intermediate, normalized)
    return _apply_overlap(raw_results, config.chunk_overlap)


def _flush_paragraph_buffer(
    acc: list[tuple[str, str]],
    buffer: str,
    strategy: str,
) -> None:
    if buffer:
        acc.append((buffer, strategy))


def _intermediate_to_results(
    items: list[tuple[str, str]],
    source: str,
) -> list[ChunkResult]:
    """Convert (text, strategy) pairs to ChunkResults with offset tracking."""
    results: list[ChunkResult] = []
    cursor = 0
    for index, (t, strategy) in enumerate(items):
        start = source.find(t, cursor)
        if start == -1:
            start = cursor
        end = start + len(t)
        results.append(
            ChunkResult(
                text=t,
                chunk_index=index,
                char_count=len(t),
                token_count=len(t.split()),
                start_char=start,
                end_char=end,
                split_strategy=strategy,
            )
        )
        cursor = end
    return results


def _fixed_chars_split(text: str, config: ChunkingConfig) -> list[ChunkResult]:
    """Split text into fixed-size chunks with offset tracking. No overlap."""
    if not text:
        return []
    results: list[ChunkResult] = []
    size = config.chunk_size
    start = 0
    index = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end - start == 0:
            break
        chunk_text = text[start:end]
        results.append(
            ChunkResult(
                text=chunk_text,
                chunk_index=index,
                char_count=len(chunk_text),
                token_count=len(chunk_text.split()),
                start_char=start,
                end_char=end,
                split_strategy="fixed_chars",
            )
        )
        start = end
        index += 1
    return results


def _apply_overlap(
    results: list[ChunkResult],
    overlap: int,
) -> list[ChunkResult]:
    """Post-process: prepend trailing chars from previous chunk."""
    if overlap <= 0 or len(results) <= 1:
        return results

    out: list[ChunkResult] = []
    for i, r in enumerate(results):
        if i == 0:
            out.append(r)
            continue
        prev = out[-1]
        actual_overlap = min(overlap, len(prev.text))
        overlap_suffix = prev.text[-actual_overlap:] if actual_overlap > 0 else ""
        new_text = overlap_suffix + r.text
        out.append(
            ChunkResult(
                text=new_text,
                chunk_index=r.chunk_index,
                char_count=len(new_text),
                token_count=len(new_text.split()),
                start_char=r.start_char,
                end_char=r.end_char,
                split_strategy=r.split_strategy,
                overlap_with_previous=actual_overlap,
            )
        )
    return out
