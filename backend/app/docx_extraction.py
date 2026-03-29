"""Ordered paragraph text extraction from DOCX (body only, no headers/footers/tables)."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError


class DocxExtractionError(Exception):
    """File missing, unreadable, or not a valid DOCX document."""


@dataclass(frozen=True)
class DocxExtractionResult:
    """Structured text suitable for later pipeline stages."""

    full_text: str
    paragraphs: list[str]


def extract_docx_from_bytes(data: bytes) -> DocxExtractionResult:
    if not data:
        raise DocxExtractionError("Файл пуст.")

    try:
        doc = Document(BytesIO(data))
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError) as exc:
        raise DocxExtractionError(
            "Файл не является корректным документом DOCX."
        ) from exc
    except OSError as exc:
        raise DocxExtractionError("Не удалось прочитать файл DOCX.") from exc

    paragraphs = [p.text.strip() for p in doc.paragraphs]
    full_text = "\n".join(paragraphs)
    return DocxExtractionResult(full_text=full_text, paragraphs=paragraphs)


def extract_docx_from_path(path: Path) -> DocxExtractionResult:
    resolved = path.resolve()
    if not resolved.is_file():
        raise DocxExtractionError("Файл не найден.")
    return extract_docx_from_bytes(resolved.read_bytes())
