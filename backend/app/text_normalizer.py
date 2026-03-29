"""Minimal, non-destructive normalization of extracted document text.

Applied after extraction and before API responses. Keeps paragraph/page
ordering and list length; does not merge structural units.
"""

from __future__ import annotations


def _unify_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_text(text: str) -> str:
    """Normalize a single text segment (paragraph, page body, or similar).

    - Trims leading/trailing whitespace
    - Normalizes ``\\r\\n`` / ``\\r`` to ``\\n``
    - Collapses runs of horizontal whitespace within each line to one space
    - Collapses three or more consecutive newlines to two (one blank line max)
    """
    if not text:
        return ""
    t = _unify_newlines(text).strip()
    if not t:
        return ""
    lines = t.split("\n")
    collapsed_lines = [" ".join(line.split()) for line in lines]
    result = "\n".join(collapsed_lines)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result.strip()


def normalize_paragraphs(paragraphs: list[str]) -> list[str]:
    """Normalize each paragraph; order and count are preserved."""
    return [normalize_text(p) for p in paragraphs]


def normalize_pages(pages: list[str]) -> list[str]:
    """Normalize each page's text; order and count are preserved."""
    return [normalize_text(p) for p in pages]


def normalized_docx_full_text(paragraphs: list[str]) -> str:
    """Build DOCX ``full_text`` from normalized paragraphs (single ``\\n`` between items)."""
    parts = normalize_paragraphs(paragraphs)
    return "\n".join(parts).strip()


def normalized_pdf_full_text(pages: list[str]) -> str:
    """Build PDF ``full_text`` from normalized pages (``\\n\\n`` between items)."""
    parts = normalize_pages(pages)
    return "\n\n".join(parts).strip()
