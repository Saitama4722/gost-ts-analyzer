"""Tests for unified document format (DOCX paragraphs / PDF pages as blocks)."""

from backend.app.document_unifier import (
    UnifiedDocument,
    unified_document_to_dict,
    unify_docx,
    unify_pdf,
)
from backend.app.text_normalizer import normalized_docx_full_text, normalized_pdf_full_text


def test_unify_docx_join_matches_normalizer() -> None:
    blocks = ["A", "", "B"]
    doc = unify_docx(blocks)
    assert isinstance(doc, UnifiedDocument)
    assert doc.blocks == ["A", "", "B"]
    assert doc.full_text == normalized_docx_full_text(blocks)


def test_unify_pdf_join_matches_normalizer() -> None:
    blocks = ["p1", "p2"]
    doc = unify_pdf(blocks)
    assert doc.blocks == ["p1", "p2"]
    assert doc.full_text == normalized_pdf_full_text(blocks)


def test_unify_copies_list_not_alias() -> None:
    blocks = ["x"]
    doc = unify_docx(blocks)
    blocks.append("y")
    assert doc.blocks == ["x"]


def test_unified_document_to_dict_keys() -> None:
    doc = unify_docx(["a", "b"])
    d = unified_document_to_dict(doc)
    assert set(d.keys()) == {"full_text", "blocks"}
    assert d["blocks"] == ["a", "b"]
