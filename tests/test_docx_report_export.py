"""Tests for minimal DOCX report export (Stage 15.3)."""

from __future__ import annotations

import zipfile
from io import BytesIO

from backend.app.reporting.docx_report_export import (
    build_analysis_docx_bytes,
    conclusion_from_payload,
    issues_from_analysis_payload,
    safe_export_filename_stem,
)


def test_safe_export_filename_stem() -> None:
    assert safe_export_filename_stem("  foo/bar/Тест.docx  ") == "Тест"
    assert safe_export_filename_stem("") == "document"


def test_issues_prefers_top_level() -> None:
    payload = {
        "issues": [{"check_key": "x", "message": "m"}],
        "report": {"issues": [{"check_key": "y", "message": "n"}]},
    }
    got = issues_from_analysis_payload(payload)
    assert len(got) == 1
    assert got[0]["check_key"] == "x"


def test_issues_falls_back_to_report() -> None:
    payload = {"report": {"issues": [{"check_key": "y", "message": "n"}]}}
    got = issues_from_analysis_payload(payload)
    assert len(got) == 1
    assert got[0]["check_key"] == "y"


def test_conclusion_from_payload() -> None:
    assert (
        conclusion_from_payload(
            {"report": {"summary": {"conclusion": "  Итог  "}}}
        )
        == "Итог"
    )
    assert conclusion_from_payload({}) == ""


def test_build_analysis_docx_bytes_zip_and_markers() -> None:
    payload = {
        "filename": "sample.docx",
        "report": {
            "summary": {"conclusion": "Проверка выполнена."},
        },
        "issues": [
            {
                "severity": "warning",
                "check_key": "vague_wording_check",
                "message": "Тестовое сообщение",
                "section_title": "Раздел 1",
                "fragment_text": "фрагмент",
                "recommendation": "исправить",
            }
        ],
    }
    raw, name = build_analysis_docx_bytes(payload)
    assert name.endswith("-report.docx")
    assert name.startswith("sample")
    assert raw[:2] == b"PK"
    zf = zipfile.ZipFile(BytesIO(raw))
    xml = zf.read("word/document.xml").decode("utf-8")
    assert "Отчёт о проверке" in xml
    assert "Проверка выполнена." in xml
    assert "Тестовое сообщение" in xml
