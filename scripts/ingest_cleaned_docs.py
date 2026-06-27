#!/usr/bin/env python3
"""Offline document ingestion — reads cleaned documents and ingests into RAG store.

Reads manifest.json from the cleaned output directory and calls
KnowledgeStore.ingest_text() for each document-level cleaned file.
RAG chunker handles final chunking.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{ROOT / 'data' / 'pipeline_ingest.db'}")

from harness.rag.store import knowledge_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest cleaned documents into RAG store.")
    parser.add_argument("--tenant-id", required=True, help="Tenant ID for document tagging.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Cleaned docs directory.")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"Error: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    docs = manifest.get("documents", [])
    if not docs:
        print("No documents to ingest.")
        return 0

    count = 0
    for doc in docs:
        cleaned_path = input_dir / doc["cleaned_path"]
        if not cleaned_path.is_file():
            print(f"Warning: cleaned file not found: {cleaned_path}", file=sys.stderr)
            continue

        text = cleaned_path.read_text(encoding="utf-8")
        metadata = {
            "document_id": doc["document_id"],
            "document_key": doc["document_key"],
            "document_version": doc.get("document_version", 1),
            "source_hash": doc["source_hash"],
            "source_filename": doc["source_filename"],
            "status": doc.get("status", "active"),
        }

        knowledge_store.ingest_text(
            title=doc["document_key"],
            text=text,
            content_type=doc["content_type"],
            source="ingestion_pipeline",
            tenant_id=args.tenant_id,
            metadata=metadata,
        )
        count += 1

    print(f"Ingested {count} document(s) for tenant '{args.tenant_id}'.")
    print(f"  Final chunking handled by KnowledgeStore (V1.4+ tenant filter compatible).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
