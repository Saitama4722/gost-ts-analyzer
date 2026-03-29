"""Stage 10.4: measurement units presence and number–unit linkage in obligation-style fragments."""

from __future__ import annotations

import re
from typing import Any

from backend.app.checks.content_match_helpers import collapse_ws_casefold
from backend.app.checks.numeric_signal_patterns import (
    DIGIT_RE,
    NUMBER_LETTER_UNIT_COMPACT,
    NUMBER_UNIT_COMPACT,
    TIME_WITH_NUMBER,
    UNIT_WITH_NUMBER,
    classify_quantitative_signals,
    is_number_unit_linked,
)
from backend.app.checks.requirement_fragments import (
    collect_fragments,
    first_obligation_span,
    is_probably_heading_line,
)

# Units or unit phrases without a required adjacent digit (collapsed text).
_STANDALONE_UNIT = re.compile(
    r"(?:"
    r"(?<![\d,\.])(?<!\d)%(?!\d)|"
    r"°\s*[cсfф](?![а-яёa-z0-9])|"
    r"мбит\s*/\s*с|мегабит\s*/\s*с|"
    r"км\s*/\s*ч|"
    r"запросов\s+в\s+секунду|операций\s+в\s+(?:секунду|минуту)|"
    r"(?<![а-яёa-z0-9])(?:гц|мгц)(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])(?:кб|мб|гб|тб)(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])байт(?:ов|а|ы)?(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])(?:мм|см|км)(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])(?:кг|мг)(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])секунд(?:а|ы|ам|ах|ою)?(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])минут(?:а|ы|ам|ах)?(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])час(?:ов|а|у|ам|ах)?(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])мсек(?![а-яёa-z0-9])|"
    r"(?<![а-яёa-z0-9])мс(?![а-яёa-z0-9])|"
    r"в\s+секундах|в\s+минутах|в\s+часах|"
    r"(?<![а-яёa-z0-9])градус(?:ов|а|е|ах)?(?![а-яёa-z0-9])"
    r")",
    re.IGNORECASE,
)


def _gather_matched_units(original: str, collapsed: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(raw: str) -> None:
        t = " ".join(raw.split())
        if len(t) > 48:
            t = t[:48].rstrip()
        k = t.casefold()
        if not k or k in seen:
            return
        seen.add(k)
        out.append(t)

    for m in TIME_WITH_NUMBER.finditer(original):
        add(m.group(0))
    for m in UNIT_WITH_NUMBER.finditer(collapsed):
        add(m.group(0))
    for m in NUMBER_UNIT_COMPACT.finditer(original):
        add(m.group(0))
    for m in NUMBER_LETTER_UNIT_COMPACT.finditer(original):
        add(m.group(0))
    for m in _STANDALONE_UNIT.finditer(collapsed):
        add(m.group(0))
    return out


def _measurement_reason(
    has_numeric_value: bool,
    has_unit: bool,
    number_unit_linked: bool,
) -> str:
    if number_unit_linked:
        return "числовое значение связано с единицей измерения"
    if has_numeric_value and has_unit:
        return "число и единица измерения присутствуют, но связь между ними неочевидна"
    if has_numeric_value and not has_unit:
        return "числовое значение обнаружено без единицы измерения"
    if not has_numeric_value and has_unit:
        return "упоминание единицы измерения без связанного числового значения"
    return "числовые значения и единицы измерения не обнаружены"


def _is_review_finding(
    has_numeric_value: bool,
    has_unit: bool,
    number_unit_linked: bool,
) -> bool:
    if number_unit_linked:
        return False
    return has_numeric_value or has_unit


def check_document_measurement_units(structure: dict[str, Any], full_text: str) -> dict[str, Any]:
    """Return ``measurement_units_check`` for obligation-style fragments (same pipeline as 10.2–10.3)."""
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

        has_numeric_value = bool(DIGIT_RE.search(frag))
        matched_units = _gather_matched_units(frag, collapsed)
        has_unit = len(matched_units) > 0
        number_unit_linked = is_number_unit_linked(frag, collapsed)

        entry: dict[str, Any] = {
            "text": frag.strip(),
            "has_numeric_value": has_numeric_value,
            "has_unit": has_unit,
            "number_unit_linked": number_unit_linked,
            "matched_units": matched_units,
            "reason": _measurement_reason(has_numeric_value, has_unit, number_unit_linked),
            "matched_signal_categories": classify_quantitative_signals(frag, collapsed),
            "fragment_index": frag_idx,
        }
        if section_title:
            entry["section_title"] = section_title
        items.append(entry)

    has_findings = any(
        _is_review_finding(
            i["has_numeric_value"],
            i["has_unit"],
            i["number_unit_linked"],
        )
        for i in items
    )

    return {
        "measurement_units_check": {
            "has_findings": has_findings,
            "item_count": len(items),
            "items": items,
        }
    }
