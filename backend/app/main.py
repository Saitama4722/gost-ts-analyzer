"""FastAPI application entrypoint for GOST TS Analyzer."""

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.app.docx_extraction import DocxExtractionError, extract_docx_from_path
from backend.app.document_unifier import unified_document_to_dict, unify_docx, unify_pdf
from backend.app.pdf_extraction import PdfExtractionError, extract_pdf_from_path
from backend.app.checks.acceptance_criteria_check import check_document_acceptance_criteria
from backend.app.checks.functional_requirements_check import check_document_functional_requirements
from backend.app.checks.nonfunctional_requirements_check import check_document_nonfunctional_requirements
from backend.app.checks.purpose_check import check_document_purpose
from backend.app.checks.scope_check import check_document_scope
from backend.app.checks.required_sections_check import check_required_sections_presence
from backend.app.checks.section_order_check import check_section_order
from backend.app.checks.structure_completeness_check import check_structure_completeness
from backend.app.checks.measurement_units_check import check_document_measurement_units
from backend.app.checks.numerical_characteristics_check import check_document_numerical_characteristics
from backend.app.checks.unverifiable_requirements_check import check_document_unverifiable_requirements
from backend.app.checks.appendix_references_check import check_document_appendix_references
from backend.app.checks.figure_references_check import check_document_figure_references
from backend.app.checks.table_references_check import check_document_table_references
from backend.app.checks.terminology_consistency_check import check_document_terminology_consistency
from backend.app.checks.duplicate_formulations_check import check_document_duplicate_formulations
from backend.app.checks.vague_wording_check import check_document_vague_wording
from backend.app.reporting.docx_report_export import (
    build_analysis_docx_bytes,
    content_disposition_attachment,
)
from backend.app.reporting.issues_builder import build_document_issues_serialized
from backend.app.reporting.report_builder import build_analysis_report
from backend.app.structure_builder import add_section_tree
from backend.app.structure_detector import detect_structure
from backend.app.structure_enricher import enrich_structure
from backend.app.text_normalizer import normalize_pages, normalize_paragraphs

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
UPLOADS_DIR = PROJECT_ROOT / "uploads"

_ALLOWED_SUFFIXES = frozenset({".docx", ".pdf"})
_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "application/x-pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


def _safe_client_filename(name: str | None) -> str:
    base = Path(name or "").name
    return base if base else "upload"


def _effective_upload_suffix(filename: str | None, content_type: str | None) -> str | None:
    """Resolve ``.docx`` / ``.pdf`` for the analysis pipeline (extension or MIME)."""
    name_suffix = Path(filename or "").suffix.lower()
    if name_suffix in _ALLOWED_SUFFIXES:
        return name_suffix
    raw_ct = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if raw_ct not in _ALLOWED_CONTENT_TYPES or name_suffix not in _ALLOWED_SUFFIXES | {""}:
        return None
    if raw_ct in ("application/pdf", "application/x-pdf"):
        return ".pdf"
    if raw_ct == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    return None

app = FastAPI(
    title="GOST TS Analyzer",
    description="Web service for analyzing technical specification documents for GOST-related compliance.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html_path = TEMPLATES_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/export/report-docx")
def export_analysis_report_docx(payload: dict[str, Any]) -> Response:
    """Build a minimal DOCX from the client-held structured analysis JSON (Stage 15.3)."""
    body, filename = build_analysis_docx_bytes(payload)
    return Response(
        content=body,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={"Content-Disposition": content_disposition_attachment(filename)},
    )


@app.post("/api/upload", response_model=None)
async def upload_document(file: UploadFile = File(...)):
    effective_suffix = _effective_upload_suffix(file.filename, file.content_type)
    if effective_suffix is None:
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={
                "status": "error",
                "message": "Unsupported file type. Only DOCX and PDF are accepted.",
            },
        )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    client_name = _safe_client_filename(file.filename)
    stored_name = f"{uuid.uuid4().hex}_{client_name}"
    uploads_resolved = UPLOADS_DIR.resolve()
    dest = (UPLOADS_DIR / stored_name).resolve()
    if not dest.is_relative_to(uploads_resolved):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Invalid filename."},
        )

    body = await file.read()
    dest.write_bytes(body)

    response: dict = {
        "status": "accepted",
        "filename": client_name,
        "content_type": file.content_type or "",
        "size": len(body),
        "stored_as": stored_name,
    }

    suffix = effective_suffix
    if suffix == ".docx":
        try:
            extracted = extract_docx_from_path(dest)
            paras = normalize_paragraphs(extracted.paragraphs)
            unified = unify_docx(paras)
            response["extraction"] = unified_document_to_dict(unified)
            raw_structure = add_section_tree(detect_structure(unified.blocks))
            enriched = enrich_structure(raw_structure, unified.blocks)
            response["structure"] = enriched
            presence = check_required_sections_presence(enriched)
            response["checks"] = {
                **presence,
                **check_section_order(enriched),
                **check_structure_completeness(enriched, presence_result=presence),
                **check_document_purpose(enriched, unified.full_text),
                **check_document_scope(enriched, unified.full_text),
                **check_document_functional_requirements(enriched, unified.full_text),
                **check_document_nonfunctional_requirements(enriched, unified.full_text),
                **check_document_acceptance_criteria(enriched, unified.full_text),
                **check_document_vague_wording(enriched, unified.full_text),
                **check_document_unverifiable_requirements(enriched, unified.full_text),
                **check_document_numerical_characteristics(enriched, unified.full_text),
                **check_document_measurement_units(enriched, unified.full_text),
                **check_document_figure_references(unified.blocks),
                **check_document_table_references(unified.blocks),
                **check_document_appendix_references(unified.blocks),
                **check_document_terminology_consistency(enriched, unified.full_text),
                **check_document_duplicate_formulations(enriched, unified.full_text),
            }
        except DocxExtractionError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "message": str(exc),
                },
            )
    elif suffix == ".pdf":
        try:
            extracted = extract_pdf_from_path(dest)
            pgs = normalize_pages(extracted.pages)
            unified = unify_pdf(pgs)
            response["extraction"] = unified_document_to_dict(unified)
            raw_structure = add_section_tree(detect_structure(unified.blocks))
            enriched = enrich_structure(raw_structure, unified.blocks)
            response["structure"] = enriched
            presence = check_required_sections_presence(enriched)
            response["checks"] = {
                **presence,
                **check_section_order(enriched),
                **check_structure_completeness(enriched, presence_result=presence),
                **check_document_purpose(enriched, unified.full_text),
                **check_document_scope(enriched, unified.full_text),
                **check_document_functional_requirements(enriched, unified.full_text),
                **check_document_nonfunctional_requirements(enriched, unified.full_text),
                **check_document_acceptance_criteria(enriched, unified.full_text),
                **check_document_vague_wording(enriched, unified.full_text),
                **check_document_unverifiable_requirements(enriched, unified.full_text),
                **check_document_numerical_characteristics(enriched, unified.full_text),
                **check_document_measurement_units(enriched, unified.full_text),
                **check_document_figure_references(unified.blocks),
                **check_document_table_references(unified.blocks),
                **check_document_appendix_references(unified.blocks),
                **check_document_terminology_consistency(enriched, unified.full_text),
                **check_document_duplicate_formulations(enriched, unified.full_text),
            }
        except PdfExtractionError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "message": str(exc),
                },
            )

    if "checks" in response:
        response["issues"] = build_document_issues_serialized(response["checks"])
        response["report"] = build_analysis_report(response["issues"])

    return response
