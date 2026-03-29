"""Stage 6.2: build a hierarchical section tree from flat ``sections`` (6.1).

Deterministic, rule-based only: level from title prefix; stack-based tree.
Does not re-scan blocks or re-detect headings.
"""

from __future__ import annotations

from typing import Any

from backend.app.rules.common_rules import NUMERIC_TITLE_PREFIX_PATTERN
from backend.app.structure_detector import _first_line, _is_numbered_heading


def section_level_from_title(title: str) -> int:
    """Level 1 for non-numbered titles; for numbered titles, count dot-separated parts."""
    fl = _first_line(title)
    if not _is_numbered_heading(fl):
        return 1
    m = NUMERIC_TITLE_PREFIX_PATTERN.match(fl.strip())
    if not m:
        return 1
    parts = [p for p in m.group(1).split(".") if p]
    return len(parts) if parts else 1


def _node(title: str, level: int, start_block: int) -> dict[str, Any]:
    return {
        "title": title,
        "level": level,
        "start_block": start_block,
        "children": [],
    }


def build_section_tree(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn flat ``sections`` into a tree using a stack (in-order, no reordering)."""
    tree: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []

    for sec in sections:
        title = str(sec["title"])
        start_block = int(sec["start_block"])
        level = section_level_from_title(title)
        node = _node(title, level, start_block)

        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if stack:
            stack[-1]["children"].append(node)
        else:
            tree.append(node)

        stack.append(node)

    return tree


def add_section_tree(structure: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``structure`` with ``tree`` added; flat ``sections`` unchanged."""
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        sections = []
    out = dict(structure)
    out["sections"] = list(sections)
    out["tree"] = build_section_tree(out["sections"])
    return out
