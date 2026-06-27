"""Pipeline orchestrator — scan → parse → clean → chunk → manifest."""

import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from harness.ingestion.cleaner import clean_text
from harness.ingestion.chunker import chunk_document
from harness.ingestion.models import Manifest, ManifestChunk, ManifestDocument
from harness.ingestion.parsers import parse_file


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".xlsx", ".xls"}


def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def run_pipeline(
    input_dir: Path,
    tenant_id: str | None = None,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> Manifest:
    """Run the full ingestion pipeline.

    Scans input_dir for supported files, parses, cleans, chunks,
    and writes manifest + cleaned documents + preview chunks.
    """
    files = sorted(
        p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    manifest = Manifest(pipeline_version="v1.5", tenant_id=tenant_id)
    total_chunks = 0

    for file_path in files:
        # Parse
        parsed = parse_file(file_path, tenant_id=tenant_id)

        # Clean
        cleaned = clean_text(parsed.text, parsed.content_type)
        source_hash = _compute_hash(parsed.text)

        # Preview chunk
        preview_chunks = chunk_document(parsed)

        doc_id = f"doc_{uuid4().hex[:12]}"
        doc_key = file_path.stem

        manifest_doc = ManifestDocument(
            document_id=doc_id,
            document_key=doc_key,
            source_hash=source_hash,
            source_filename=file_path.name,
            content_type=parsed.content_type,
            cleaned_path=f"documents/{doc_key}.cleaned.md",
            chunk_count=len(preview_chunks),
        )
        manifest.documents.append(manifest_doc)

        for ci, pc in enumerate(preview_chunks):
            manifest.chunks.append(ManifestChunk(
                document_id=doc_id,
                chunk_index=ci,
                text=pc["text"],
                char_count=pc["char_count"],
                token_count=pc["token_count"],
            ))
            total_chunks += 1

        # Write cleaned document and preview chunks
        if output_dir and not dry_run:
            docs_dir = output_dir / "documents"
            chunks_dir = output_dir / "chunks"
            docs_dir.mkdir(parents=True, exist_ok=True)
            chunks_dir.mkdir(parents=True, exist_ok=True)

            (docs_dir / f"{doc_key}.cleaned.md").write_text(cleaned, encoding="utf-8")

            for ci, pc in enumerate(preview_chunks):
                chunk_path = chunks_dir / f"{doc_key}_{ci:03d}.json"
                chunk_path.write_text(json.dumps(pc, ensure_ascii=False), encoding="utf-8")

    # Write manifest
    if output_dir and not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "manifest.json").write_text(
            manifest.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"Pipeline: {len(files)} file(s) processed, {total_chunks} preview chunk(s)")
    if dry_run:
        print("[dry-run] No files were written.")
    else:
        print(f"Output: {output_dir}")
    return manifest
