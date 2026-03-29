"""Stage 8.3: structural completeness summary from required-section presence.

Derives counts and a boolean summary from Stage 8.1 output (same ``present`` /
``missing`` keys). Does not re-run heading matching when ``presence_result`` is
provided. Optional flags describe empty or sparse skeleton signals only.
"""

from __future__ import annotations

from typing import Any

from backend.app.checks.required_sections_check import check_required_sections_presence


def _flat_section_heading_count(structure: dict[str, Any]) -> int:
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        return 0
    n = 0
    for sec in sections:
        if isinstance(sec, dict) and sec.get("title") is not None:
            n += 1
    return n


def check_structure_completeness(
    structure: dict[str, Any],
    *,
    presence_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize structural completeness from ``required_sections_check`` data.

    ``is_complete`` is true only when no required sections are missing (including
    the case ``required_total == 0``).

    If ``presence_result`` is omitted, runs ``check_required_sections_presence`` once.
    """
    if presence_result is None:
        presence_result = check_required_sections_presence(structure)

    rsc = presence_result.get("required_sections_check") or {}
    present = rsc.get("present") if isinstance(rsc.get("present"), list) else []
    missing = rsc.get("missing") if isinstance(rsc.get("missing"), list) else []

    present = [str(k) for k in present]
    missing = [str(k) for k in missing]

    required_total = len(present) + len(missing)
    present_count = len(present)
    missing_count = len(missing)

    if required_total == 0:
        completeness_ratio = 1.0
    else:
        completeness_ratio = round(present_count / required_total, 4)

    is_complete = missing_count == 0

    headings_with_title = _flat_section_heading_count(structure)
    no_sections_detected = headings_with_title == 0
    structure_sparse = required_total > 0 and present_count == 0

    return {
        "structure_completeness_check": {
            "is_complete": is_complete,
            "required_total": required_total,
            "present_count": present_count,
            "missing_count": missing_count,
            "completeness_ratio": completeness_ratio,
            "present": present,
            "missing": missing,
            "no_sections_detected": no_sections_detected,
            "structure_sparse": structure_sparse,
        }
    }
