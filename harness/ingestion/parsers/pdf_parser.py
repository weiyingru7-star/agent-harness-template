"""Minimal .pdf parser — text-only, no OCR."""

from pathlib import Path

from harness.ingestion.models import ParsedDoc


def parse_pdf(path: Path, tenant_id: str | None = None) -> ParsedDoc:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        raise ImportError(
            "pdfminer.six is required for PDF parsing. "
            "Install: pip install pdfminer.six"
        )
    text = extract_text(str(path))
    return ParsedDoc(
        source_filename=path.name,
        content_type="pdf",
        text=text,
        metadata={"source": "pdfminer"},
        tenant_id=tenant_id,
    )
