"""Stage 12.2: deterministic repeated and near-duplicate formulation detection.

Uses the same fragment pipeline as Stage 10 obligation-style scans: section ``content_text``
when present, otherwise ``full_text``. Headings and very short fragments are skipped.
Level A: exact match after case/whitespace/punctuation-insensitive normalization.
Level B: high lexical overlap (token Jaccard and/or SequenceMatcher), conservative thresholds.
"""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.checks.requirement_fragments import collect_fragments, is_probably_heading_line

_PUNCT_RUN = re.compile(r"[^\w\s]+", re.UNICODE)
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

_NEAR_JACCARD = 0.88
_NEAR_JACCARD_RELAX = 0.80
_NEAR_SEQ = 0.89
_MIN_TOKENS = 5
_MIN_TOKEN_OVERLAP = 5


def _exact_normalization_key(fragment: str) -> str:
    c = collapse_ws_casefold(fragment)
    c = _PUNCT_RUN.sub(" ", c)
    return " ".join(c.split())


def _token_set(collapsed: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(collapsed))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    if not u:
        return 1.0
    return len(a & b) / len(u)


def _sequence_ratio_on_stripped(collapsed_a: str, collapsed_b: str) -> float:
    sa = " ".join(_PUNCT_RUN.sub(" ", collapsed_a).split())
    sb = " ".join(_PUNCT_RUN.sub(" ", collapsed_b).split())
    if not sa and not sb:
        return 1.0
    return SequenceMatcher(None, sa, sb).ratio()


def _near_duplicate_score(
    key_a: str,
    key_b: str,
    collapsed_a: str,
    collapsed_b: str,
) -> tuple[bool, float]:
    if key_a == key_b:
        return False, 0.0
    ta = _token_set(collapsed_a)
    tb = _token_set(collapsed_b)
    if len(ta) < _MIN_TOKENS or len(tb) < _MIN_TOKENS:
        return False, 0.0
    overlap = len(ta & tb)
    if overlap < _MIN_TOKEN_OVERLAP:
        return False, 0.0
    jac = _jaccard(ta, tb)
    seq = _sequence_ratio_on_stripped(collapsed_a, collapsed_b)
    sim = max(jac, seq)
    ok = jac >= _NEAR_JACCARD or (jac >= _NEAR_JACCARD_RELAX and seq >= _NEAR_SEQ)
    return ok, float(sim)


def check_document_duplicate_formulations(structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Return ``duplicate_formulations_check`` with exact and conservative near-duplicate items."""
    rows: list[tuple[str | None, int, str, str]] = []
    for section_title, frag_idx, frag in collect_fragments(structure, full_text):
        collapsed = collapse_ws_casefold(frag)
        if not collapsed:
            continue
        if is_probably_heading_line(frag, collapsed):
            continue
        rows.append((section_title, frag_idx, frag.strip(), collapsed))

    if not rows:
        return {
            "duplicate_formulations_check": {
                "has_findings": False,
                "item_count": 0,
                "items": [],
            }
        }

    by_key: dict[str, list[tuple[str | None, int, str]]] = defaultdict(list)
    for section_title, frag_idx, orig, _collapsed in rows:
        k = _exact_normalization_key(orig)
        if not k:
            continue
        by_key[k].append((section_title, frag_idx, orig))

    items: list[dict[str, Any]] = []

    for k, occs in sorted(by_key.items(), key=lambda kv: (kv[0],)):
        if len(occs) < 2:
            continue
        occs_sorted = sorted(occs, key=lambda t: (t[1], t[2]))
        rep = occs_sorted[0][2]
        idxs = sorted({fi for _, fi, _ in occs_sorted})
        titles = sorted({st for st, _, _ in occs_sorted if st})
        entry: dict[str, Any] = {
            "kind": "exact_duplicate",
            "text": rep,
            "occurrences": len(occs_sorted),
            "reason": "в документе повторяется одинаковая формулировка",
            "fragment_indexes": idxs,
        }
        if titles:
            entry["section_titles"] = titles
        items.append(entry)

    key_meta: dict[str, tuple[int, str, str]] = {}
    for doc_ord, (_section_title, frag_idx, orig, collapsed) in enumerate(rows):
        k = _exact_normalization_key(orig)
        if not k:
            continue
        if k not in key_meta:
            key_meta[k] = (doc_ord, orig, collapsed)

    ordered_keys = sorted(key_meta.items(), key=lambda kv: (kv[1][0], kv[0]))
    for i, (ka, (ord_a, text_a, col_a)) in enumerate(ordered_keys):
        for kb, (ord_b, text_b, col_b) in ordered_keys[i + 1 :]:
            ok, sim = _near_duplicate_score(ka, kb, col_a, col_b)
            if not ok:
                continue
            ta, tb = (text_a, text_b) if ord_a <= ord_b else (text_b, text_a)
            near: dict[str, Any] = {
                "kind": "near_duplicate",
                "text_a": ta,
                "text_b": tb,
                "similarity": round(sim, 3),
                "reason": "обнаружены очень похожие формулировки",
            }
            items.append(near)

    def _sort_key(it: dict[str, Any]) -> tuple[int, str, str]:
        kind_order = 0 if it["kind"] == "exact_duplicate" else 1
        t = it.get("text") or it.get("text_a") or ""
        u = it.get("text_b") or ""
        return (kind_order, t, u)

    items.sort(key=_sort_key)

    return {
        "duplicate_formulations_check": {
            "has_findings": len(items) > 0,
            "item_count": len(items),
            "items": items,
        }
    }
