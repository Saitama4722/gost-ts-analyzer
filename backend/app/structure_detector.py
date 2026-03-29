"""Rule-based detection of headings / section starts from unified ``blocks``.

Stage 6.1 only: no hierarchy, no content splitting, no GOST validation.
"""

from __future__ import annotations

from typing import Any

from backend.app.rules.common_rules import (
    MAX_UPPERCASE_HEADING_BLOCK_LEN,
    MEASUREMENT_FIRST_TOKENS,
    NUMBERED_HEADING_DEEP_PATTERN,
    NUMBERED_HEADING_DOT_PATTERN,
    NUMBERED_HEADING_TWO_PART_PATTERN,
)
from backend.app.rules.section_rules import SECTION_KEYWORDS_FOR_HEADING_DETECTION


def _first_alnum_token_after_prefix(line: str, prefix_end: int) -> str:
    rest = line[prefix_end:].strip()
    if not rest:
        return ""
    token = rest.split()[0].strip(".,;:!?\"'()[]")
    return token


def _first_line(block: str) -> str:
    return block.strip().split("\n", 1)[0].strip()


def _is_numbered_heading(first_line: str) -> bool:
    if NUMBERED_HEADING_DOT_PATTERN.match(first_line):
        return True
    if NUMBERED_HEADING_DEEP_PATTERN.match(first_line):
        return True
    m = NUMBERED_HEADING_TWO_PART_PATTERN.match(first_line)
    if not m:
        return False
    first_tok = _first_alnum_token_after_prefix(first_line, m.end())
    if first_tok.lower() in MEASUREMENT_FIRST_TOKENS:
        return False
    return True


def _is_uppercase_heading(block: str) -> bool:
    s = block.strip()
    if not s or len(s) >= MAX_UPPERCASE_HEADING_BLOCK_LEN:
        return False
    if s != s.upper():
        return False
    return any(ch.isalpha() for ch in s)


def _is_keyword_heading(block: str) -> bool:
    s = block.strip()
    return s.lower() in SECTION_KEYWORDS_FOR_HEADING_DETECTION


def detect_structure(blocks: list[str]) -> dict[str, Any]:
    """Return ``{"sections": [{"title": str, "start_block": int}, ...]}``.

    Each detected heading starts a section; indices are 0-based block indices.
    """
    sections: list[dict[str, str | int]] = []
    for i, block in enumerate(blocks):
        if not block or not block.strip():
            continue
        s = block.strip()
        fl = _first_line(block)

        title: str | None = None
        if _is_numbered_heading(fl):
            title = fl
        elif _is_uppercase_heading(s):
            title = s
        elif _is_keyword_heading(s):
            title = s

        if title is not None:
            sections.append({"title": title, "start_block": i})

    return {"sections": sections}
