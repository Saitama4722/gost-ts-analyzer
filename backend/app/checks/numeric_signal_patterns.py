"""Shared numeric / measurability signal patterns for Stage 9.7 and Stage 10.x checks."""

from __future__ import annotations

import re

from backend.app.checks.content_match_helpers import phrase_search_key
from backend.app.rules.acceptance_criteria_rules import ACCEPTANCE_CRITERIA_TEXT_PHRASES

DIGIT_RE = re.compile(r"\d")

# Time or duration when tied to a number (original fragment, flexible spacing).
TIME_WITH_NUMBER = re.compile(
    r"\d[\d\s,\.]*\s*(?:"
    r"мсек|мс\b|"
    r"сек(?:унд|унды|унд)?|сек\.|с\.(?!\w)|"
    r"мин(?:ут)?|мин\.|"
    r"час(?:а|ов)?|ч\.|"
    r"дн(?:ей|я)?|дн\.|"
    r"недел(?:и|ь|ю|ями)?|"
    r"месяц(?:а|ев)?|"
    r"лет|год(?:а|у|ов)?"
    r")",
    re.IGNORECASE,
)

# Common concrete units / metrics after a number (collapsed).
UNIT_WITH_NUMBER = re.compile(
    r"\d[\d\s,\.]*\s*(?:"
    r"%|проц|"
    r"с\.(?!\w)|"
    r"гц|мгц|кг|мг|г\b|"
    r"км/ч|км\b|мм\b|см\b|м[²³]?\b|градус|°\s*[cсfф]\b|"
    r"бит|байт|кб\b|мб\b|гб\b|тб\b|"
    r"мбит\s*/\s*с|мегабит\s*/\s*с|"
    r"вт\b|ма\b|ом\b|"
    r"рпс|tps|qps"
    r")",
    re.IGNORECASE,
)

# Number immediately followed by a unit token (no required space), original text.
NUMBER_UNIT_COMPACT = re.compile(
    r"\d+(?:[,\.]\d+)?(?:"
    r"мсек|мс|"
    r"сек(?:унд|унды|унд)?|сек\.|"
    r"с\.|"
    r"мин(?:ут)?|мин\.|"
    r"ч(?:ас(?:а|ов)?)?|ч\.|"
    r"гб|мб|кб|тб|"
    r"гц|мгц|"
    r"кг|мг|"
    r"мм|см|км|"
    r"км/ч|мбит/с|мегабит/с|"
    r"%|°[cс]|°\s*[cс]"
    r")(?![а-яёa-z0-9])",
    re.IGNORECASE,
)

# Bare "с" / "м" / "г" as seconds / meters / grams when glued to digits (e.g. 2с, 10м, 5г).
NUMBER_LETTER_UNIT_COMPACT = re.compile(
    r"\d+(?:[,\.]\d+)?[смг](?![а-яёa-z0-9])",
    re.IGNORECASE,
)

THRESHOLD_SUBSTRINGS: tuple[str, ...] = (
    "не менее",
    "не более",
    "не меньше",
    "не больше",
    "не свыше",
    "не ниже",
    "не выше",
    "не дольше",
    "не позже",
    "не раньше",
    "в пределах",
    "диапазон",
)

RATE_SUBSTRINGS: tuple[str, ...] = (
    "запросов в секунду",
    "операций в секунду",
    "операций в минуту",
    "в секунду",
)

# "от 18 до 24", "от X до Y" with numeric ends (case-folded collapsed text).
RANGE_FROM_TO = re.compile(
    r"от\s+\d[\d\s,\.]*\s+до\s+\d",
    re.IGNORECASE,
)

# Numeric interval with dash (Unicode or ASCII hyphen).
RANGE_DASH_INTERVAL = re.compile(r"\d[\d\s,\.]*\s*[–—−-]\s*\d[\d\s,\.]")

# Comparison operators between quantities (collapsed).
COMPARISON_OPS = re.compile(r">=|<=|≥|≤")
COMPARISON_BETWEEN_NUMBERS = re.compile(r"\d[\d\s,\.]*\s*[<>]\s*\d[\d\s,\.]*")


def _has_explicit_acceptance_wording(collapsed: str) -> bool:
    for phrase in ACCEPTANCE_CRITERIA_TEXT_PHRASES:
        key = phrase_search_key(phrase)
        if key and key in collapsed:
            return True
    return False


def _has_threshold_phrase(collapsed: str) -> bool:
    return any(s in collapsed for s in THRESHOLD_SUBSTRINGS)


def _has_rate_phrase(collapsed: str) -> bool:
    return any(s in collapsed for s in RATE_SUBSTRINGS)


def _has_comparison_signal(collapsed: str) -> bool:
    if COMPARISON_OPS.search(collapsed):
        return True
    if COMPARISON_BETWEEN_NUMBERS.search(collapsed):
        return True
    return False


def _has_range_signal(collapsed: str) -> bool:
    if RANGE_FROM_TO.search(collapsed):
        return True
    if RANGE_DASH_INTERVAL.search(collapsed):
        return True
    return False


_DEGREE_C_RE = re.compile(r"°\s*[cсfф]\b", re.IGNORECASE)


def is_number_unit_linked(original: str, collapsed: str) -> bool:
    """True when a numeric value is tied to a measurement unit in a practical way (Stage 10.4)."""
    if TIME_WITH_NUMBER.search(original):
        return True
    if UNIT_WITH_NUMBER.search(collapsed):
        return True
    if NUMBER_UNIT_COMPACT.search(original):
        return True
    if NUMBER_LETTER_UNIT_COMPACT.search(original):
        return True
    if DIGIT_RE.search(original) and _has_rate_phrase(collapsed):
        return True
    if _has_range_signal(collapsed) and (
        TIME_WITH_NUMBER.search(original)
        or UNIT_WITH_NUMBER.search(collapsed)
        or "%" in original
        or _DEGREE_C_RE.search(original)
    ):
        return True
    return False


def has_verifiability_signals(original: str, collapsed: str) -> bool:
    """True if fragment shows measurable / verifiable cues (Stage 10.2)."""
    if DIGIT_RE.search(original):
        return True
    if "%" in original:
        return True
    if TIME_WITH_NUMBER.search(original):
        return True
    if UNIT_WITH_NUMBER.search(collapsed):
        return True
    if NUMBER_UNIT_COMPACT.search(original):
        return True
    if NUMBER_LETTER_UNIT_COMPACT.search(original):
        return True
    if _has_threshold_phrase(collapsed):
        return True
    if _has_rate_phrase(collapsed):
        return True
    if _has_explicit_acceptance_wording(collapsed):
        return True
    if _has_comparison_signal(collapsed):
        return True
    if _has_range_signal(collapsed):
        return True
    return False


def classify_quantitative_signals(original: str, collapsed: str) -> list[str]:
    """Category tags for explicit quantitative characteristics (Stage 10.3)."""
    found: set[str] = set()
    if DIGIT_RE.search(original):
        found.add("number")
    if "%" in original:
        found.add("percentage")
    if TIME_WITH_NUMBER.search(original):
        found.add("duration")
    if UNIT_WITH_NUMBER.search(collapsed):
        found.add("unit")
    if NUMBER_UNIT_COMPACT.search(original) or NUMBER_LETTER_UNIT_COMPACT.search(original):
        found.add("unit")
    if _has_threshold_phrase(collapsed):
        found.add("threshold")
    if _has_rate_phrase(collapsed):
        found.add("rate")
    if _has_comparison_signal(collapsed):
        found.add("comparison")
    if _has_range_signal(collapsed):
        found.add("range")
    return sorted(found)
