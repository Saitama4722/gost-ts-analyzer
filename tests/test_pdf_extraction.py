"""Tests for PDF text extraction."""

from io import BytesIO
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from backend.app.main import UPLOADS_DIR, app
from backend.app.pdf_extraction import (
    PdfExtractionError,
    extract_pdf_from_bytes,
    extract_pdf_from_path,
)


def _blank_pdf_bytes() -> bytes:
    buf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buf)
    return buf.getvalue()


def _pdf_bytes_with_page_texts(*page_texts: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for i, text in enumerate(page_texts):
        if i > 0:
            c.showPage()
        c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


def test_extract_pdf_preserves_page_order_and_full_text() -> None:
    data = _pdf_bytes_with_page_texts("Alpha", "Beta")
    result = extract_pdf_from_bytes(data)
    assert result.pages == ["Alpha", "Beta"]
    assert result.full_text == "Alpha\n\nBeta"


def test_extract_pdf_blank_page_yields_empty_strings() -> None:
    result = extract_pdf_from_bytes(_blank_pdf_bytes())
    assert result.pages == [""]
    assert result.full_text == ""


def test_extract_pdf_empty_file_raises() -> None:
    with pytest.raises(PdfExtractionError, match="Empty"):
        extract_pdf_from_bytes(b"")


def test_extract_pdf_invalid_bytes_raises() -> None:
    with pytest.raises(PdfExtractionError, match="Not a valid"):
        extract_pdf_from_bytes(b"not a pdf")


def test_extract_pdf_truncated_header_raises() -> None:
    with pytest.raises(PdfExtractionError, match="Not a valid"):
        extract_pdf_from_bytes(b"%PDF-1.4\n")


def test_extract_pdf_from_path_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope.pdf"
    with pytest.raises(PdfExtractionError, match="not found"):
        extract_pdf_from_path(missing)


def test_upload_pdf_extensionless_name_with_pdf_mime_runs_full_pipeline() -> None:
    """MIME + empty extension must still run checks/issues (regression: no bare 'accepted')."""
    data = _pdf_bytes_with_page_texts("Line1", "Line2")
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("specification", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert "checks" in body
    assert "issues" in body
    assert "report" in body
    assert isinstance(body["issues"], list)


def test_upload_pdf_includes_extraction() -> None:
    data = _pdf_bytes_with_page_texts("Line1", "Line2")
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("spec.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["extraction"]["blocks"] == ["Line1", "Line2"]
    assert body["extraction"]["full_text"] == "Line1\n\nLine2"
    assert "structure" in body
    assert "checks" in body
    assert "issues" in body
    assert "report" in body
    assert isinstance(body["issues"], list)
    stored = body["stored_as"]
    assert (UPLOADS_DIR / stored).is_file()


def test_upload_pdf_corrupt_returns_422() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("bad.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload.get("message")


def test_upload_pdf_plain_text_disguised_as_pdf_returns_422() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "report.pdf",
                b"This is not a PDF document.",
                "application/pdf",
            )
        },
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_upload_pdf_docx_payload_with_pdf_extension_returns_422() -> None:
    """Valid DOCX bytes under a .pdf name must not pass PDF extraction."""
    doc = Document()
    doc.add_paragraph("Раздел")
    buf = BytesIO()
    doc.save(buf)
    data = buf.getvalue()
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("disguised.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_upload_two_pdf_files_sequentially_independent() -> None:
    """Two uploads in a row must not share state; ASCII text matches default PDF font."""
    client = TestClient(app)
    first = _pdf_bytes_with_page_texts("FirstRun")
    second = _pdf_bytes_with_page_texts("SecondRun")
    r1 = client.post(
        "/api/upload",
        files={"file": ("one.pdf", first, "application/pdf")},
    )
    r2 = client.post(
        "/api/upload",
        files={"file": ("two.pdf", second, "application/pdf")},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    b1 = r1.json()
    b2 = r2.json()
    assert b1["stored_as"] != b2["stored_as"]
    assert b1["extraction"]["full_text"] == "FirstRun"
    assert b2["extraction"]["full_text"] == "SecondRun"
    assert (UPLOADS_DIR / b1["stored_as"]).is_file()
    assert (UPLOADS_DIR / b2["stored_as"]).is_file()


def test_upload_pdf_blank_page_accepted() -> None:
    data = _blank_pdf_bytes()
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("emptyish.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["extraction"]["full_text"] == ""
    assert body["extraction"]["blocks"] == [""]
    assert "issues" in body
    assert "report" in body


def test_upload_pdf_empty_body_returns_422() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("zero.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"
