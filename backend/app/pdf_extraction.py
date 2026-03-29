"""Plain text extraction from PDF (no OCR, no layout reconstruction)."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PasswordType, PdfReader
from pypdf.errors import EmptyFileError, PdfReadError


class PdfExtractionError(Exception):
    """File missing, unreadable, invalid PDF, or text cannot be extracted."""


@dataclass(frozen=True)
class PdfExtractionResult:
    """Structured text suitable for later pipeline stages."""

    full_text: str
    pages: list[str]


def _minimal_page_cleanup(raw: str | None) -> str:
    if not raw:
        return ""
    return "\n".join(line.rstrip() for line in raw.splitlines()).strip()


def extract_pdf_from_bytes(data: bytes) -> PdfExtractionResult:
    if not data:
        raise PdfExtractionError("Empty file.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)
    except (PdfReadError, EmptyFileError) as exc:
        raise PdfExtractionError("Not a valid PDF document.") from exc
    except OSError as exc:
        raise PdfExtractionError("Could not read PDF file.") from exc

    if reader.is_encrypted:
        try:
            decrypt_result = reader.decrypt("")
        except PdfReadError as exc:
            raise PdfExtractionError("Encrypted PDF cannot be read without a password.") from exc
        if decrypt_result == PasswordType.NOT_DECRYPTED:
            raise PdfExtractionError("Encrypted PDF cannot be read without a password.")

    pages: list[str] = []
    try:
        for page in reader.pages:
            try:
                raw = page.extract_text()
            except Exception as exc:
                raise PdfExtractionError("Could not extract text from PDF.") from exc
            pages.append(_minimal_page_cleanup(raw))
    except PdfReadError as exc:
        raise PdfExtractionError("Not a valid PDF document.") from exc

    full_text = "\n\n".join(pages).strip()
    return PdfExtractionResult(full_text=full_text, pages=pages)


def extract_pdf_from_path(path: Path) -> PdfExtractionResult:
    resolved = path.resolve()
    if not resolved.is_file():
        raise PdfExtractionError("File not found.")
    return extract_pdf_from_bytes(resolved.read_bytes())
