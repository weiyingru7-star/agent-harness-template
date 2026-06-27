"""Minimal .txt parser."""

from pathlib import Path

from harness.ingestion.models import ParsedDoc


def parse_txt(path: Path, tenant_id: str | None = None) -> ParsedDoc:
    text = path.read_text(encoding="utf-8", errors="replace")
    return ParsedDoc(
        source_filename=path.name,
        content_type="txt",
        text=text,
        tenant_id=tenant_id,
    )
