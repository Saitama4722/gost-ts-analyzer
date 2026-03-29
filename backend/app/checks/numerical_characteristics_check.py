"""Stage 10.3: detect explicit quantitative signals in obligation-style requirement fragments."""

from __future__ import annotations

from typing import Any

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.checks.numeric_signal_patterns import classify_quantitative_signals
from backend.app.checks.requirement_fragments import (
    collect_fragments,
    first_obligation_span,
    is_probably_heading_line,
)


def check_document_numerical_characteristics(structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Return ``numerical_characteristics_check`` for requirement-like fragments and numeric signals.

    Uses ``content_text`` per section when any section has body text; otherwise ``full_text``.
    """
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

        if first_obligation_span(collapsed) is None:
            continue

        seen_keys.add(dedupe_key)
        signals = classify_quantitative_signals(frag, collapsed)
        numeric_ok = bool(signals)

        entry: dict[str, Any] = {
            "text": frag.strip(),
            "has_numeric_characteristics": numeric_ok,
            "matched_signals": signals,
            "fragment_index": frag_idx,
        }
        if section_title:
            entry["section_title"] = section_title
        items.append(entry)

    any_numeric = any(i["has_numeric_characteristics"] for i in items)

    return {
        "numerical_characteristics_check": {
            "has_numeric_findings": any_numeric,
            "item_count": len(items),
            "items": items,
        }
    }
