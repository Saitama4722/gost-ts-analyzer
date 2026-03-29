"""Stage 10.2: deterministic detection of requirement-like text without measurable criteria.

Uses enriched section ``content_text`` when available; otherwise falls back to ``full_text``.
Conservative heuristics: obligation modality + absence of numeric / threshold / unit / time signals.
"""

from __future__ import annotations

from typing import Any

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.checks.numeric_signal_patterns import has_verifiability_signals
from backend.app.checks.requirement_fragments import (
    collect_fragments,
    first_obligation_span,
    is_probably_heading_line,
    obligation_marker_text,
)


def check_document_unverifiable_requirements(structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Return ``unverifiable_requirements_check`` with conservative obligation + no-metrics findings."""
    items: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for section_title, frag_idx, frag in collect_fragments(structure, full_text):
        collapsed = collapse_ws_casefold(frag)
        if not collapsed:
            continue
        dedupe_key = collapsed
        if dedupe_key in seen_keys:
            continue

        if is_probably_heading_line(frag, collapsed):
            continue

        span = first_obligation_span(collapsed)
        if span is None:
            continue

        if has_verifiability_signals(frag, collapsed):
            continue

        seen_keys.add(dedupe_key)
        start, end = span
        marker = obligation_marker_text(frag, collapsed, start, end)

        entry: dict[str, Any] = {
            "text": frag.strip(),
            "reason": "формулировка требования без измеримых критериев",
            "obligation_marker": marker,
            "fragment_index": frag_idx,
        }
        if section_title:
            entry["section_title"] = section_title
        items.append(entry)

    return {
        "unverifiable_requirements_check": {
            "has_findings": len(items) > 0,
            "items": items,
            "item_count": len(items),
        }
    }
