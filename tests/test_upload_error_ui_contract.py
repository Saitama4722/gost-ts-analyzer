"""
API contract for /api/upload error responses consumed by the web UI.

The client (static/js/upload.js) relies on specific status codes and JSON
fields; these tests document that contract without a browser.
"""

from io import BytesIO

import pytest
from docx import Document
from fastapi.testclient import TestClient

from backend.app.main import app


def _minimal_docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph("x")
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_upload_missing_file_field_returns_422_detail_shape(client: TestClient) -> None:
    """FastAPI 422: missing `file` — client maps detail[].loc containing 'file'."""
    response = client.post("/api/upload", data={})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "missing"
        and isinstance(item.get("loc"), list)
        and "file" in item["loc"]
        for item in body["detail"]
    )


def test_upload_unsupported_type_returns_415_error_status(client: TestClient) -> None:
    response = client.post(
        "/api/upload",
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
    payload = response.json()
    assert payload.get("status") == "error"
    assert "message" in payload


def test_upload_corrupt_docx_returns_422_russian_message(client: TestClient) -> None:
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "bad.docx",
                b"PK\x03\x04broken",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload.get("status") == "error"
    msg = payload.get("message", "")
    assert isinstance(msg, str) and msg.strip()
    assert any("\u0400" <= ch <= "\u04ff" for ch in msg)


def test_upload_success_response_shape_for_ui(client: TestClient) -> None:
    """Success uses status accepted; empty issues list is not an error."""
    data = _minimal_docx_bytes()
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "ok.docx",
                data,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "accepted"
    assert "issues" in payload
    assert isinstance(payload["issues"], list)


def test_upload_docx_extensionless_name_with_docx_mime_includes_issues(client: TestClient) -> None:
    """Same pipeline as named .docx when extension is inferred from Content-Type only."""
    data = _minimal_docx_bytes()
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "technical_spec",
                data,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "accepted"
    assert "checks" in payload
    assert "issues" in payload
    assert "report" in payload
