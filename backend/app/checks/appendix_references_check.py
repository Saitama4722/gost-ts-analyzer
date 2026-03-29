"""Stage 11.3: consistency between in-text appendix mentions and heading declarations."""

from __future__ import annotations

import re
from typing import Any

from backend.app.checks.reference_number_utils import numbering_gaps_in_range

# Typical order for Cyrillic appendix letters (deterministic gap detection).
_CYRILLIC_APPENDIX_LETTER_ORDER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
_ORDER_INDEX = {ch: i for i, ch in enumerate(_CYRILLIC_APPENDIX_LETTER_ORDER)}

# Line-start heading: «Приложение А …», «Приложение 1 …» (normalized, stripped line).
# Excludes «Приложение к …» (attachment to a contract, not label «К»).
_DECLARATION_LINE = re.compile(
    r"^приложение\s+(?!к\b)(?:([А-ЯЁ])(?![а-яёa-z0-9])|(\d+)(?!\d))",
    re.IGNORECASE,
)

# Running text: grammatical cases; «приложения» only with guard against «приложения к …».
_MENTION_MAIN = re.compile(
    r"(?<![а-яёa-z0-9])(?:приложение|приложении|приложению)\s+(?!к\b)"
    r"(?:([А-ЯЁ])(?![а-яёa-z0-9])|(\d+)(?!\d))",
    re.IGNORECASE,
)

_MENTION_GENITIVE_PLURAL = re.compile(
    r"(?<![а-яёa-z0-9])приложения\s+(?!к\s)"
    r"(?:([А-ЯЁ])(?![а-яёa-z0-9])|(\d+)(?!\d))",
    re.IGNORECASE,
)


def _label_from_groups(letter: str | None, digits: str | None) -> str | None:
    if digits:
        return str(int(digits))
    if letter:
        return letter.upper()
    return None


def _sort_labels(labels: set[str]) -> list[str]:
    letters: list[str] = []
    numbers: list[int] = []
    other: list[str] = []
    for raw in labels:
        if raw.isdigit():
            numbers.append(int(raw))
        elif len(raw) == 1 and raw in _ORDER_INDEX:
            letters.append(raw)
        else:
            other.append(raw)
    letters.sort(key=lambda c: _ORDER_INDEX.get(c, 999))
    numbers.sort()
    other.sort()
    return [str(n) for n in numbers] + letters + other


def _cyrillic_letter_sequence_gaps(declared_letters: set[str]) -> list[str]:
    indices = sorted({_ORDER_INDEX[ch] for ch in declared_letters if ch in _ORDER_INDEX})
    if len(indices) < 2:
        return []
    lo, hi = indices[0], indices[-1]
    present = {ch for ch in declared_letters if ch in _ORDER_INDEX}
    return [
        _CYRILLIC_APPENDIX_LETTER_ORDER[i]
        for i in range(lo, hi + 1)
        if _CYRILLIC_APPENDIX_LETTER_ORDER[i] not in present
    ]


def _numeric_label_gaps(declared_numeric: set[str]) -> list[int]:
    nums = {int(x) for x in declared_numeric if x.isdigit()}
    return numbering_gaps_in_range(nums)


def check_document_appendix_references(blocks: list[str]) -> dict[str, Any]:
    """Compare appendix labels mentioned in text with labels declared in heading lines.

    Declaration lines match only at the start of a line (after strip). Those lines are
    skipped for mention extraction so a heading is not counted as an in-text reference.

    ``blocks`` must be normalized unified document blocks (paragraphs or pages).
    """
    mentioned: set[str] = set()
    declared: set[str] = set()
    declaration_counts: dict[str, int] = {}
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
                label = _label_from_groups(decl_m.group(1), decl_m.group(2))
                if label is None:
                    continue
                declared.add(label)
                declaration_counts[label] = declaration_counts.get(label, 0) + 1
                declarations_detail.append(
                    {
                        "label": label,
                        "block_index": block_index,
                        "line_index": line_index,
                        "heading_line": line[:500],
                    }
                )
                continue
            for rx in (_MENTION_MAIN, _MENTION_GENITIVE_PLURAL):
                for m in rx.finditer(line):
                    label = _label_from_groups(m.group(1), m.group(2))
                    if label is None:
                        continue
                    mentioned.add(label)
                    mentions_detail.append(
                        {
                            "label": label,
                            "block_index": block_index,
                            "line_index": line_index,
                            "mention_text": m.group(0).strip(),
                            "line": line[:500],
                        }
                    )

    duplicate_declarations = sorted(l for l, c in declaration_counts.items() if c > 1)
    declared_sorted = _sort_labels(declared)
    mentioned_sorted = _sort_labels(mentioned)
    missing_declarations = _sort_labels(mentioned - declared)
    unreferenced_appendices = _sort_labels(declared - mentioned)

    declared_letters = {x for x in declared if len(x) == 1 and x in _ORDER_INDEX}
    declared_numeric = {x for x in declared if x.isdigit()}
    cyrillic_letter_sequence_gaps = _cyrillic_letter_sequence_gaps(declared_letters)
    numeric_appendix_gaps = _numeric_label_gaps(declared_numeric)

    has_issues = bool(
        missing_declarations or unreferenced_appendices or duplicate_declarations
    )

    return {
        "appendix_references_check": {
            "mentioned_labels": mentioned_sorted,
            "declared_labels": declared_sorted,
            "missing_declarations": missing_declarations,
            "unreferenced_appendices": unreferenced_appendices,
            "duplicate_declarations": duplicate_declarations,
            "cyrillic_letter_sequence_gaps": cyrillic_letter_sequence_gaps,
            "numeric_appendix_gaps": numeric_appendix_gaps,
            "has_issues": has_issues,
            "mentions": mentions_detail,
            "declarations": declarations_detail,
        }
    }
