"""Shared helpers for scanning obligation-style fragments in Stage 10 checks."""

from __future__ import annotations

import re
from typing import Any

# Obligation / normative modality (case-folded matching).
OBLIGATION_RE = re.compile(
    r"(?<![0-9a-zа-яё_])(?:"
    r"должны|должна|должно|должен|"
    r"обязаны|обязана|обязано|обязан|"
    r"необходимо|требуется|следует"
    r")(?![0-9a-zа-яё_])",
    re.IGNORECASE,
)

MIN_FRAGMENT_LEN = 30


def split_sentence_fragments(text: str) -> list[str]:
    """Split on sentence-ending punctuation; whitespace normalized to spaces."""
    single_line = " ".join(str(text).split())
    if not single_line:
        return []
    parts = re.split(r"(?<=[.!?…])\s+", single_line)
    return [p.strip() for p in parts if p.strip()]


def collect_fragments(structure: dict[str, Any], full_text: str) -> list[tuple[str | None, int, str]]:
    """Return ``(section_title, index_in_section, fragment)`` in deterministic order."""
    out: list[tuple[str | None, int, str]] = []
    sections = structure.get("sections")
    if not isinstance(sections, list):
        sections = []
    any_body = False
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        raw_title = sec.get("title")
        title_s = str(raw_title).strip() if raw_title is not None else ""
        body = sec.get("content_text") or ""
        body_s = str(body).strip()
        if not body_s:
            continue
        any_body = True
        frags = split_sentence_fragments(body_s)
        for i, frag in enumerate(frags):
            out.append((title_s or None, i, frag))
    if not any_body:
        for i, frag in enumerate(split_sentence_fragments(full_text or "")):
            out.append((None, i, frag))
    return out


def first_obligation_span(collapsed: str) -> tuple[int, int] | None:
    m = OBLIGATION_RE.search(collapsed)
    if not m:
        return None
    return m.start(), m.end()


def obligation_marker_text(original: str, collapsed: str, start: int, end: int) -> str:
    """Map case-folded span to substring of ``original`` when lengths align; else use span slice."""
    if len(original) == len(collapsed):
        return original[start:end].strip()
    return collapsed[start:end].strip()


def is_probably_heading_line(fragment: str, collapsed: str) -> bool:
    """Skip very short fragments and numbered section stubs (not full sentences)."""
    st = fragment.strip()
    if len(st) < MIN_FRAGMENT_LEN:
        return True
    if (
        len(st) < 72
        and re.match(r"^\s*[\d\.]+\s+\S", st)
        and not re.search(r"[.!?…]\s*$", st)
        and not OBLIGATION_RE.search(collapsed)
    ):
        return True
    return False
