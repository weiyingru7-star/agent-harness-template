from harness.rag.chunking import chunk_text_with_strategy
from harness.rag.chunking_types import ChunkingConfig


def test_short_text_produces_one_chunk() -> None:
    config = ChunkingConfig()
    results = chunk_text_with_strategy("Short text.", config)

    assert len(results) == 1
    assert results[0].text == "Short text."
    assert results[0].chunk_index == 0


def test_multi_paragraph_produces_multiple_chunks() -> None:
    text = "\n\n".join([f"Paragraph {i} with some content." for i in range(20)])
    config = ChunkingConfig(chunk_size=100)
    results = chunk_text_with_strategy(text, config)

    assert len(results) > 1
    for i, r in enumerate(results):
        assert r.chunk_index == i


def test_chunk_index_is_contiguous() -> None:
    text = "\n\n".join([f"Para {i} content here." for i in range(30)])
    config = ChunkingConfig(chunk_size=80)
    results = chunk_text_with_strategy(text, config)

    indices = [r.chunk_index for r in results]
    assert indices == list(range(len(results)))


def test_overlap_is_applied() -> None:
    text = "\n\n".join([f"Paragraph number {i} with enough text to trigger overlap." for i in range(10)])
    config = ChunkingConfig(chunk_size=100, chunk_overlap=30)
    results = chunk_text_with_strategy(text, config)

    if len(results) > 1:
        assert results[1].overlap_with_previous > 0
        assert results[0].text[-results[1].overlap_with_previous:] in results[1].text


def test_no_overlap_by_default() -> None:
    text = "\n\n".join([f"Paragraph {i} with filler text here." for i in range(8)])
    config = ChunkingConfig(chunk_size=100)
    results = chunk_text_with_strategy(text, config)

    if len(results) > 1:
        assert results[1].overlap_with_previous == 0


def test_paragraph_split_strategy() -> None:
    text = "Short para A\n\nShort para B\n\nShort para C"
    config = ChunkingConfig(chunk_size=500)
    results = chunk_text_with_strategy(text, config)

    assert len(results) >= 1
    for r in results:
        assert r.split_strategy == "paragraph"


def test_long_paragraph_fallback_to_fixed_chars() -> None:
    long_text = "word " * 500  # ~2500 chars, exceeds 500*1.2=600
    config = ChunkingConfig(chunk_size=100)
    results = chunk_text_with_strategy(long_text, config)

    assert len(results) > 1
    fallback_chunks = [r for r in results if r.split_strategy == "fixed_chars"]
    assert fallback_chunks


def test_fixed_chars_split_strategy() -> None:
    text = "A" * 1500
    config = ChunkingConfig(chunk_size=500, split_by="fixed_chars")
    results = chunk_text_with_strategy(text, config)

    assert len(results) == 3
    for r in results:
        assert r.split_strategy == "fixed_chars"


def test_char_count_and_token_count_are_accurate() -> None:
    text = "Hello world\n\nThis is a test."
    config = ChunkingConfig()
    results = chunk_text_with_strategy(text, config)

    assert len(results) >= 1
    for r in results:
        assert r.char_count == len(r.text)
        assert r.token_count == len(r.text.split())


def test_start_end_char_track_offsets() -> None:
    text = "AAA\n\nBBB\n\nCCC"
    config = ChunkingConfig(chunk_size=500)
    results = chunk_text_with_strategy(text, config)

    assert len(results) == 1
    assert results[0].start_char == 0
    assert results[0].end_char == len(text)


def test_ingested_chunks_have_chunk_metadata() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    file_resp = client.post(
        "/api/files/upload",
        files={"file": ("meta.md", b"# Title\n\nParagraph one.\n\nParagraph two.", "text/markdown")},
    )
    file_id = file_resp.json()["id"]

    resp = client.post(
        "/api/knowledge/ingest",
        json={"file_id": file_id, "chunking_config": {"chunk_size": 50, "chunk_overlap": 10}},
    )
    assert resp.status_code == 201
    chunks = resp.json()["chunks"]
    assert len(chunks) > 0
    meta = chunks[0].get("chunk_metadata", {})
    assert "start_char" in meta
    assert "end_char" in meta
    assert "split_strategy" in meta
    assert "chunk_size" in meta
    assert "chunk_overlap" in meta


def test_ingest_without_chunking_config_uses_default() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    file_resp = client.post(
        "/api/files/upload",
        files={"file": ("default.md", b"Default chunking test.", "text/markdown")},
    )
    file_id = file_resp.json()["id"]

    resp = client.post("/api/knowledge/ingest", json={"file_id": file_id})
    assert resp.status_code == 201
    assert len(resp.json()["chunks"]) == 1
