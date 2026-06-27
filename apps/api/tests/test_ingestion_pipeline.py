"""Tests for V1.5 Ingestion Pipeline — models, parsers, cleaner, chunker, CLI.

All tests use tmp_path — no files written to repo directories.
"""

import json
from pathlib import Path

import pytest

from harness.ingestion.cleaner import clean_text, _collapse_blank_lines, _strip_isolated_page_numbers
from harness.ingestion.models import (
    Manifest,
    ManifestChunk,
    ManifestDocument,
    ParsedDoc,
)
from harness.ingestion.parsers import parse_file
from harness.ingestion.parsers.txt_parser import parse_txt
from harness.ingestion.parsers.md_parser import parse_md


# ── Model defaults ─────────────────────────────────────────────────


def test_model_defaults_not_shared() -> None:
    """metadata, chunks, chunk_metadata use Field(default_factory)."""
    d1 = ManifestDocument(document_id="a", document_key="a", source_hash="h1",
                          source_filename="a.txt", content_type="txt",
                          cleaned_path="a/a.md", chunk_count=0)
    d2 = ManifestDocument(document_id="b", document_key="b", source_hash="h2",
                          source_filename="b.txt", content_type="txt",
                          cleaned_path="b/b.md", chunk_count=0)
    # Shared references would cause mutation across instances
    d1.metadata["key"] = "val1"
    assert "key" not in d2.metadata


def test_manifest_document_fields() -> None:
    doc = ManifestDocument(
        document_id="doc_001", document_key="readme", source_hash="abc123",
        source_filename="readme.md", content_type="md",
        cleaned_path="documents/readme.cleaned.md", chunk_count=5,
    )
    assert doc.document_id == "doc_001"
    assert doc.document_version == 1
    assert doc.status == "active"
    assert doc.metadata == {}


def test_manifest_chunk_fields() -> None:
    chunk = ManifestChunk(document_id="doc_001", chunk_index=0, text="hello world",
                          char_count=11, token_count=2)
    assert chunk.chunk_index == 0
    assert chunk.text == "hello world"


def test_manifest_round_trip() -> None:
    m = Manifest(tenant_id="t1")
    m.documents.append(
        ManifestDocument(document_id="d1", document_key="k1", source_hash="h",
                         source_filename="f.txt", content_type="txt",
                         cleaned_path="f.md", chunk_count=1)
    )
    m.chunks.append(
        ManifestChunk(document_id="d1", chunk_index=0, text="x", char_count=1)
    )
    data = json.loads(m.model_dump_json())
    assert data["tenant_id"] == "t1"
    assert len(data["documents"]) == 1
    assert len(data["chunks"]) == 1


# ── Parsers ────────────────────────────────────────────────────────


def test_parse_txt(tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("Hello world", encoding="utf-8")
    doc = parse_txt(f)
    assert doc.content_type == "txt"
    assert "Hello world" in doc.text
    assert doc.source_filename == "hello.txt"


def test_parse_md(tmp_path: Path) -> None:
    f = tmp_path / "readme.md"
    f.write_text("# Title\n\nContent.\n", encoding="utf-8")
    doc = parse_md(f)
    assert doc.content_type == "md"
    assert "# Title" in doc.text


def test_parse_file_dispatch(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("test", encoding="utf-8")
    doc = parse_file(f, tenant_id="t1")
    assert doc.tenant_id == "t1"
    assert doc.content_type == "txt"


def test_parse_unsupported_extension(tmp_path: Path) -> None:
    f = tmp_path / "bad.ppt"
    f.write_text("bad", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        parse_file(f)


# ── Cleaner ────────────────────────────────────────────────────────


def test_clean_collapse_blank_lines() -> None:
    result = _collapse_blank_lines("a\n\n\n\nb")
    assert result == "a\n\nb"


def test_clean_strip_page_numbers() -> None:
    result = _strip_isolated_page_numbers("header\n   3   \nfooter")
    assert "3" not in result


def test_clean_txt_basic() -> None:
    result = clean_text("  hello  \n\n\n\nworld  ", "txt")
    assert "hello" in result
    assert "world" in result
    assert "\n\n\n" not in result


def test_clean_empty_returns_empty() -> None:
    assert clean_text("  \n  ", "txt") == ""


# ── Pipeline dry-run ────────────────────────────────────────────────


def test_pipeline_dry_run_no_input_dir(tmp_path: Path) -> None:
    """Dry-run with non-existent input dir still works."""
    from harness.ingestion.pipeline import run_pipeline
    manifest = run_pipeline(
        input_dir=tmp_path / "nonexistent",
        tenant_id="test",
        output_dir=tmp_path / "out",
        dry_run=True,
    )
    assert len(manifest.documents) == 0


def test_pipeline_with_text_file(tmp_path: Path) -> None:
    src = tmp_path / "raw"
    src.mkdir()
    (src / "hello.txt").write_text("Hello pipeline world.", encoding="utf-8")

    out = tmp_path / "cleaned"
    from harness.ingestion.pipeline import run_pipeline
    manifest = run_pipeline(
        input_dir=src, tenant_id="t1", output_dir=out, dry_run=False,
    )
    assert len(manifest.documents) == 1
    assert manifest.documents[0].content_type == "txt"
    assert manifest.documents[0].chunk_count >= 1
    assert (out / "documents").is_dir()
    assert (out / "chunks").is_dir()
    assert (out / "manifest.json").is_file()


# ── KnowledgeStore metadata integration ─────────────────────────────


def test_ingest_text_accepts_metadata(tmp_path: Path) -> None:
    """ingest_text with metadata writes metadata into document + chunk metadata."""
    from harness.rag.store import knowledge_store
    resp = knowledge_store.ingest_text(
        title="MetaTest",
        text="Metadata test document for ingestion pipeline.",
        tenant_id="t1",
        metadata={"source_hash": "abc", "document_key": "meta_test", "status": "active"},
    )
    assert resp.document.metadata.get("tenant_id") == "t1"
    assert resp.document.metadata.get("source_hash") == "abc"
    assert resp.document.metadata.get("document_key") == "meta_test"
    # Chunks should also carry tenant_id
    for chunk in resp.chunks:
        assert chunk.chunk_metadata.get("tenant_id") == "t1"


# ── Backward compatibility ─────────────────────────────────────────


def test_old_ingest_text_still_works() -> None:
    """ingest_text without metadata/tenant_id preserves old behavior."""
    from harness.rag.store import knowledge_store
    resp = knowledge_store.ingest_text(
        title="Legacy", text="Legacy document without tenant.",
    )
    assert resp.document.title == "Legacy"
    assert len(resp.chunks) >= 1


def test_old_runs_unchanged() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.post("/api/runs", json={"input": "old style"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "completed"
