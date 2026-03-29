"""Stage 11.2: consistency between in-text table mentions and caption declarations."""

from __future__ import annotations

import re
from typing import Any

from backend.app.checks.reference_number_utils import numbering_gaps_in_range, sorted_unique_ints

# Line-start: «Таблица N …», «Табл. N …» (normalized text, stripped per line).
_DECLARATION_LINE = re.compile(
    r"^(?:таблица|табл\.)\s*(\d+)",
    re.IGNORECASE,
)

# Running text: keyword before the number; caption lines are skipped first.
_MENTION = re.compile(
    r"(?<![а-яёa-z0-9])(?:таблица|таблице|таблицы|таблицу|таблицей|табл\.)\s*(\d+)(?!\d)",
    re.IGNORECASE,
)


def check_document_table_references(blocks: list[str]) -> dict[str, Any]:
    """Compare table numbers mentioned in text with numbers declared in caption lines.

    Caption lines are detected only at the start of a line (after strip). Those lines are
    excluded from mention extraction so a caption is not counted as an ordinary reference.

    ``blocks`` must be the normalized unified document blocks (paragraphs or pages).
    """
    mentioned: set[int] = set()
    declared: set[int] = set()
    declaration_counts: dict[int, int] = {}
    mentions_detail: list[dict[str, Any]] = []
    declarations_detail: list[dict[str, Any]] = []

    for block_index, block in enumerate(blocks):
        if not block or not block.strip():
            continue
        lines = block.split("\n")
        for line_index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue
            decl_m = _DECLARATION_LINE.match(line)
            if decl_m:
                num = int(decl_m.group(1))
                declared.add(num)
                declaration_counts[num] = declaration_counts.get(num, 0) + 1
                declarations_detail.append(
                    {
                        "number": num,
                        "block_index": block_index,
                        "line_index": line_index,
                        "caption_line": line[:500],
                    }
                )
                continue
            for m in _MENTION.finditer(line):
                num = int(m.group(1))
                mentioned.add(num)
                mentions_detail.append(
                    {
                        "number": num,
                        "block_index": block_index,
                        "line_index": line_index,
                        "mention_text": m.group(0).strip(),
                        "line": line[:500],
                    }
                )

    duplicate_declarations = sorted(n for n, c in declaration_counts.items() if c > 1)
    declared_sorted = sorted_unique_ints(declared)
    mentioned_sorted = sorted_unique_ints(mentioned)
    declared_set = declared
    mentioned_set = mentioned
    missing_declarations = sorted_unique_ints(mentioned_set - declared_set)
    unreferenced_tables = sorted_unique_ints(declared_set - mentioned_set)
    caption_numbering_gaps = numbering_gaps_in_range(declared_set)

    has_issues = bool(
        missing_declarations or unreferenced_tables or duplicate_declarations
    )

    return {
        "table_references_check": {
            "mentioned_numbers": mentioned_sorted,
            "declared_numbers": declared_sorted,
            "missing_declarations": missing_declarations,
            "unreferenced_tables": unreferenced_tables,
            "duplicate_declarations": duplicate_declarations,
            "caption_numbering_gaps": caption_numbering_gaps,
            "has_issues": has_issues,
            "mentions": mentions_detail,
            "declarations": declarations_detail,
        }
    }
