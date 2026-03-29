"""Unified document shape for DOCX and PDF after normalization.

``blocks`` are paragraphs for DOCX and pages for PDF. Join rules for
``full_text`` match ``text_normalizer.normalized_docx_full_text`` /
``normalized_pdf_full_text`` (single ``\\n`` vs ``\\n\\n`` between blocks).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnifiedDocument:
    """Internal representation shared by all downstream stages."""

    full_text: str
    blocks: list[str]


def unify_docx(normalized_blocks: list[str]) -> UnifiedDocument:
    """DOCX: one block per body paragraph; ``full_text`` joins with ``\\n``."""
    blocks = list(normalized_blocks)
    full_text = "\n".join(blocks).strip()
    return UnifiedDocument(full_text=full_text, blocks=blocks)


def unify_pdf(normalized_blocks: list[str]) -> UnifiedDocument:
    """PDF: one block per page; ``full_text`` joins with ``\\n\\n``."""
    blocks = list(normalized_blocks)
    full_text = "\n\n".join(blocks).strip()
    return UnifiedDocument(full_text=full_text, blocks=blocks)


def unified_document_to_dict(doc: UnifiedDocument) -> dict[str, str | list[str]]:
    return {"full_text": doc.full_text, "blocks": doc.blocks}
