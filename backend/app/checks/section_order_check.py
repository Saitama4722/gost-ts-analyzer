"""Stage 8.2: required-section order vs template order (structural only).

Uses ``REQUIRED_SECTION_TEMPLATES`` / ``REQUIRED_SECTIONS`` for expected order and the
same heading normalization as Stage 8.1. Missing sections do not fail the order check.
"""

from __future__ import annotations

from typing import Any

from backend.app.checks.required_sections_check import (
    _detected_title_normalized_for_match,
    key_to_normalized_forms,
    resolve_norm_to_required_key,
)
from backend.app.rules.section_rules import REQUIRED_SECTIONS


def _detected_required_keys_in_document_order(structure: dict[str, Any]) -> list[str]:
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        return []

    forms_by_key = key_to_normalized_forms()
    seen: set[str] = set()
    order: list[str] = []

    for sec in sections:
        if not isinstance(sec, dict):
            continue
        t = sec.get("title")
        if t is None:
            continue
        norm = _detected_title_normalized_for_match(str(t))
        key = resolve_norm_to_required_key(norm, forms_by_key)
        if key is None or key in seen:
            continue
        seen.add(key)
        order.append(key)

    return order


def check_section_order(structure: dict[str, Any]) -> dict[str, Any]:
    """Return whether detected required sections follow template-relative order.

    Non-required headings and gaps between required sections are ignored. Only the
    subsequence of first occurrences of required keys (in flat ``sections`` order)
    is compared to the template order restricted to those keys.
    """
    detected_order = _detected_required_keys_in_document_order(structure)
    detected_set = frozenset(detected_order)
    expected_order_subset = [k for k in REQUIRED_SECTIONS if k in detected_set]

    is_correct = detected_order == expected_order_subset
    violations: list[dict[str, Any]] = []
    if not is_correct:
        for i, (exp, got) in enumerate(zip(expected_order_subset, detected_order)):
            if exp != got:
                violations.append(
                    {
                        "index": i,
                        "expected_key": exp,
                        "found_key": got,
                    }
                )
                break

    return {
        "section_order_check": {
            "is_correct": is_correct,
            "detected_order": detected_order,
            "expected_order_subset": expected_order_subset,
            "violations": violations,
        }
    }
