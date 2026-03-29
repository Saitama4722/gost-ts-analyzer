"""Stage 9.5: deterministic presence check for acceptance-criteria / verifiability signals."""

from __future__ import annotations

from typing import Any

from backend.app.checks.content_match_helpers import collapse_ws_casefold, phrase_search_key
from backend.app.checks.required_sections_check import (
    _detected_title_normalized_for_match,
    _normalize_heading_text,
)
from backend.app.rules.acceptance_criteria_rules import (
    ACCEPTANCE_CRITERIA_SECTION_HEADINGS,
    ACCEPTANCE_CRITERIA_TEXT_PHRASES,
)


def _normalized_ac_heading_norms() -> frozenset[str]:
    return frozenset(_normalize_heading_text(h) for h in ACCEPTANCE_CRITERIA_SECTION_HEADINGS)


def _canonical_ac_heading(norm: str) -> str:
    for h in ACCEPTANCE_CRITERIA_SECTION_HEADINGS:
        if _normalize_heading_text(h) == norm:
            return h
    return norm


def check_document_acceptance_criteria(structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Return ``acceptance_criteria_check`` from section titles first, then body phrases.

    ``structure`` is the enriched structure (flat ``sections`` with ``title``).
    ``full_text`` is normalized unified document text (same source as API ``extraction``).
    """
    not_found: dict[str, Any] = {
        "acceptance_criteria_check": {
            "is_present": False,
            "match_type": None,
            "matched_signal": None,
            "source": None,
        }
    }

    ac_norms = _normalized_ac_heading_norms()
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    for sec in sections:
        if not isinstance(sec, dict):
            continue
        t = sec.get("title")
        if t is None:
            continue
        norm = _detected_title_normalized_for_match(str(t))
        if norm in ac_norms:
            canonical = _canonical_ac_heading(norm)
            return {
                "acceptance_criteria_check": {
                    "is_present": True,
                    "match_type": "section_title",
                    "matched_signal": canonical,
                    "source": {"section_title": canonical},
                }
            }

    collapsed = collapse_ws_casefold(full_text or "")
    if not collapsed:
        return not_found

    for phrase in ACCEPTANCE_CRITERIA_TEXT_PHRASES:
        key = phrase_search_key(phrase)
        if not key:
            continue
        idx = collapsed.find(key)
        if idx < 0:
            continue
        lo = max(0, idx - 30)
        hi = min(len(collapsed), idx + len(key) + 120)
        excerpt = collapsed[lo:hi].strip()
        if hi < len(collapsed):
            excerpt = f"{excerpt} ..."
        return {
            "acceptance_criteria_check": {
                "is_present": True,
                "match_type": "text_phrase",
                "matched_signal": phrase,
                "source": {"text_excerpt": excerpt},
            }
        }

    return not_found
