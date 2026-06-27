"""Text cleaner — removes noise while preserving content."""

import re
import unicodedata


def clean_text(text: str, content_type: str = "txt") -> str:
    """Clean text based on content type. Returns cleaned text."""
    if content_type in ("txt", "md"):
        text = _normalize_unicode(text)
        text = _collapse_blank_lines(text)
        text = _strip_trailing_whitespace(text)
    elif content_type == "pdf":
        text = _normalize_unicode(text)
        text = _strip_isolated_page_numbers(text)
        text = _collapse_blank_lines(text)
    elif content_type == "docx":
        text = _normalize_unicode(text)
        text = _collapse_blank_lines(text)
    elif content_type in ("csv", "xlsx"):
        text = _normalize_unicode(text)
    return text.strip() + "\n" if text.strip() else ""


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _strip_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _strip_isolated_page_numbers(text: str) -> str:
    lines = text.split("\n")
    filtered = [line for line in lines if not re.fullmatch(r"\s*\d+\s*", line)]
    return "\n".join(filtered)
