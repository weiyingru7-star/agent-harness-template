"""Minimal .md parser — preserves headings."""

from pathlib import Path

from harness.ingestion.models import ParsedDoc


def parse_md(path: Path, tenant_id: str | None = None) -> ParsedDoc:
    text = path.read_text(encoding="utf-8", errors="replace")
    return ParsedDoc(
        source_filename=path.name,
        content_type="md",
        text=text,
        metadata={"format": "markdown"},
        tenant_id=tenant_id,
    )
