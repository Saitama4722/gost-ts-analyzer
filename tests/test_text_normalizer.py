"""Tests for extracted text normalization."""

from backend.app.text_normalizer import (
    normalize_pages,
    normalize_paragraphs,
    normalize_text,
    normalized_docx_full_text,
    normalized_pdf_full_text,
)


def test_normalize_text_empty_and_whitespace_only() -> None:
    assert normalize_text("") == ""
    assert normalize_text("   \t  ") == ""
    assert normalize_text("\r\n\r\n") == ""


def test_normalize_text_unifies_line_endings_and_trims() -> None:
    assert normalize_text("  a\r\nb\rc  ") == "a\nb\nc"


def test_normalize_text_collapses_spaces_within_lines() -> None:
    assert normalize_text("hello    world\t\ttest") == "hello world test"


def test_normalize_text_collapses_excessive_blank_lines() -> None:
    assert normalize_text("a\n\n\n\nb") == "a\n\nb"


def test_normalize_paragraphs_preserves_count_and_order() -> None:
    inp = ["  x  ", "", "y\r\nz"]
    assert normalize_paragraphs(inp) == ["x", "", "y\nz"]


def test_normalize_pages_preserves_count_and_order() -> None:
    inp = ["p1", "  \n  ", "q  q"]
    assert normalize_pages(inp) == ["p1", "", "q q"]


def test_normalized_docx_full_text_join() -> None:
    assert normalized_docx_full_text(["A", "", "B"]) == "A\n\nB"


def test_normalized_pdf_full_text_join() -> None:
    assert normalized_pdf_full_text(["A", "B"]) == "A\n\nB"


def test_normalized_full_text_strips_outer_whitespace() -> None:
    assert normalized_docx_full_text(["  hi  "]) == "hi"
    assert normalized_pdf_full_text(["  hi  "]) == "hi"
