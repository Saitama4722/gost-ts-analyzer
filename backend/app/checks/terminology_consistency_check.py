"""Stage 12.1: glossary-driven terminology consistency (distinct variants per term)."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, TypedDict

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.rules.common_rules import GLOSSARY_CANONICAL_TERMS, GlossaryTermEntry


class _RawMatch(TypedDict):
    start: int
    end: int
    alias: str


def _alias_pattern(alias: str) -> re.Pattern[str]:
    """Whole-alias match with Unicode word-boundary guards (same idea as vague_wording_check)."""
    parts = alias.strip().split()
    if not parts:
        return re.compile(r"(?!x)x")
    inner = r"\s+".join(re.escape(p) for p in parts)
    return re.compile(rf"(?<!\w){inner}(?!\w)")


def _collect_raw_matches_for_term(collapsed: str, entry: GlossaryTermEntry) -> list[_RawMatch]:
    raw: list[_RawMatch] = []
    for alias in entry["aliases"]:
        a = alias.strip()
        if not a:
            continue
        pat = _alias_pattern(a)
        for m in pat.finditer(collapsed):
            raw.append({"start": m.start(), "end": m.end(), "alias": a})
    return raw


def _select_non_overlapping(raw: list[_RawMatch]) -> list[_RawMatch]:
    """Prefer longer spans, then leftmost; drop overlaps (avoids counting «интерфейс» inside longer alias)."""
    ordered = sorted(raw, key=lambda r: (-(r["end"] - r["start"]), r["start"], r["alias"]))
    kept: list[_RawMatch] = []
    for m in ordered:
        overlaps = any(not (m["end"] <= k["start"] or m["start"] >= k["end"]) for k in kept)
        if not overlaps:
            kept.append(m)
    kept.sort(key=lambda r: (r["start"], r["end"], r["alias"]))
    return kept


def _excerpt(collapsed: str, start: int, end: int, context_before: int = 40, context_after: int = 120) -> str:
    lo = max(0, start - context_before)
    hi = min(len(collapsed), end + context_after)
    piece = collapsed[lo:hi].strip()
    if lo > 0:
        piece = f"... {piece}"
    if hi < len(collapsed):
        piece = f"{piece} ..."
    return piece


def check_document_terminology_consistency(_structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Detect glossary terms for which more than one configured variant appears in the document.

    Uses ``GLOSSARY_CANONICAL_TERMS`` only. Scans normalized logical text via the same
    whitespace collapse and case-folding as other content checks. Single-variant usage
    (including only a non-canonical alias) does not produce a finding.
    """
    collapsed = collapse_ws_casefold(full_text or "")
    if not collapsed:
        return {
            "terminology_consistency_check": {
                "has_findings": False,
                "item_count": 0,
                "items": [],
            }
        }

    items: list[dict[str, Any]] = []

    for entry in GLOSSARY_CANONICAL_TERMS:
        raw = _collect_raw_matches_for_term(collapsed, entry)
        if not raw:
            continue
        selected = _select_non_overlapping(raw)
        if not selected:
            continue

        counts = Counter(m["alias"] for m in selected)
        distinct_aliases = sorted(counts.keys())
        if len(distinct_aliases) < 2:
            continue

        first = min(selected, key=lambda m: (m["start"], m["end"], m["alias"]))
        items.append(
            {
                "term_key": entry["key"],
                "canonical": entry["canonical"],
                "used_variants": list(distinct_aliases),
                "preferred_variant": entry["canonical"],
                "reason": "для одного термина использованы разные варианты наименования",
                "occurrence_count_by_variant": {a: counts[a] for a in distinct_aliases},
                "example_snippet": _excerpt(collapsed, first["start"], first["end"]),
            }
        )

    items.sort(key=lambda it: (it["term_key"],))

    return {
        "terminology_consistency_check": {
            "has_findings": len(items) > 0,
            "item_count": len(items),
            "items": items,
        }
    }
