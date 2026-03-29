"""Stage 10.1: deterministic vague / weakly verifiable wording signals (dictionary only)."""

from __future__ import annotations

import re
from typing import Any, TypedDict

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.rules.common_rules import FORBIDDEN_VAGUE_PHRASES, VaguePhraseEntry


class _RawMatch(TypedDict):
    start: int
    end: int
    phrase: str
    entry: VaguePhraseEntry


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    """Whole-phrase match with simple Unicode word-boundary guards (no lookinside tokens)."""
    parts = phrase.strip().split()
    if not parts:
        return re.compile(r"(?!x)x")  # matches nothing
    inner = r"\s+".join(re.escape(p) for p in parts)
    return re.compile(rf"(?<!\w){inner}(?!\w)")


def _collect_raw_matches(collapsed: str) -> list[_RawMatch]:
    raw: list[_RawMatch] = []
    for entry in FORBIDDEN_VAGUE_PHRASES:
        phrase = entry["phrase"].strip()
        if not phrase:
            continue
        pat = _phrase_pattern(phrase)
        for m in pat.finditer(collapsed):
            raw.append(
                {
                    "start": m.start(),
                    "end": m.end(),
                    "phrase": phrase,
                    "entry": entry,
                }
            )
    return raw


def _select_non_overlapping(raw: list[_RawMatch]) -> list[_RawMatch]:
    """Prefer longer spans, then leftmost; drop matches that overlap a kept span."""
    ordered = sorted(raw, key=lambda r: (-(r["end"] - r["start"]), r["start"], r["phrase"]))
    kept: list[_RawMatch] = []
    for m in ordered:
        overlaps = any(
            not (m["end"] <= k["start"] or m["start"] >= k["end"]) for k in kept
        )
        if not overlaps:
            kept.append(m)
    kept.sort(key=lambda r: (r["start"], r["end"], r["phrase"]))
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


def check_document_vague_wording(_structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Scan normalized ``full_text`` for Stage 7.3 dictionary phrases.

    ``structure`` is accepted for API symmetry with other content checks; scanning
    uses ``full_text`` only (same normalization as 9.x: collapse whitespace, casefold).
    """
    collapsed = collapse_ws_casefold(full_text or "")
    if not collapsed:
        return {
            "vague_wording_check": {
                "has_findings": False,
                "findings": [],
                "finding_count": 0,
            }
        }

    raw = _collect_raw_matches(collapsed)
    selected = _select_non_overlapping(raw)

    findings: list[dict[str, Any]] = []
    for m in selected:
        entry = m["entry"]
        findings.append(
            {
                "phrase": m["phrase"],
                "match_type": "dictionary_phrase",
                "text_excerpt": _excerpt(collapsed, m["start"], m["end"]),
                "source_kind": "full_text",
                "category": entry["type"],
                "description": entry["description"],
            }
        )

    return {
        "vague_wording_check": {
            "has_findings": len(findings) > 0,
            "findings": findings,
            "finding_count": len(findings),
        }
    }
