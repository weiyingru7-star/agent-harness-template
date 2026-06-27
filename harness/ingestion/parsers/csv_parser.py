"""Minimal .csv parser — header + rows as structured text."""

import csv
import io
from pathlib import Path

from harness.ingestion.models import ParsedDoc


def parse_csv(path: Path, tenant_id: str | None = None) -> ParsedDoc:
    raw = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None:
        return ParsedDoc(
            source_filename=path.name,
            content_type="csv",
            text=raw,
            tenant_id=tenant_id,
        )
    lines = [f"Columns: {', '.join(reader.fieldnames)}"]
    for i, row in enumerate(reader):
        parts = [f"{k}: {v}" for k, v in row.items() if v.strip()]
        lines.append(f"Row {i}: {'; '.join(parts)}")
    return ParsedDoc(
        source_filename=path.name,
        content_type="csv",
        text="\n".join(lines),
        metadata={"columns": reader.fieldnames, "row_count": i + 1},
        tenant_id=tenant_id,
    )
