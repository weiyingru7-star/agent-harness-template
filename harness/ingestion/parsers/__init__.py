"""Parser registry and file dispatch."""

from pathlib import Path

from harness.ingestion.models import ParsedDoc
from harness.ingestion.parsers.txt_parser import parse_txt
from harness.ingestion.parsers.md_parser import parse_md


PARSERS: dict[str, object] = {
    ".txt": parse_txt,
    ".md": parse_md,
}


def parse_file(path: Path, tenant_id: str | None = None) -> ParsedDoc:
    """Parse a single file into a ParsedDoc. Raises ValueError on unknown type."""
    ext = path.suffix.lower()

    # Try to lazy-import optional parsers
    if ext == ".pdf":
        from harness.ingestion.parsers.pdf_parser import parse_pdf as p
    elif ext == ".docx":
        from harness.ingestion.parsers.docx_parser import parse_docx as p
    elif ext in (".csv",):
        from harness.ingestion.parsers.csv_parser import parse_csv as p
    elif ext in (".xlsx", ".xls"):
        from harness.ingestion.parsers.xlsx_parser import parse_xlsx as p
    else:
        p = PARSERS.get(ext)

    if p is None:
        raise ValueError(f"Unsupported file type: {ext}")

    return p(path, tenant_id=tenant_id)
