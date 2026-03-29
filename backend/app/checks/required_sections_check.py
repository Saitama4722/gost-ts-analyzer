"""Stage 8.1: required-section presence from built structure + section rules.

Uses ``REQUIRED_SECTION_TEMPLATES`` only (no duplicate lists). Matching is
normalized string equality on heading text after optional numeric-prefix strip.
"""

from __future__ import annotations

from typing import Any

from backend.app.rules.common_rules import NUMERIC_TITLE_PREFIX_PATTERN
from backend.app.rules.section_rules import REQUIRED_SECTIONS, REQUIRED_SECTION_TEMPLATES
from backend.app.structure_detector import _first_line, _is_numbered_heading


def _normalize_heading_text(s: str) -> str:
    return " ".join(s.split()).casefold()


def _detected_title_normalized_for_match(title: str) -> str:
    fl = _first_line(str(title))
    if _is_numbered_heading(fl):
        m = NUMERIC_TITLE_PREFIX_PATTERN.match(fl.strip())
        if m:
            rest = fl[m.end() :].lstrip(". ")
            return _normalize_heading_text(rest)
    return _normalize_heading_text(fl)


def _template_normalized_forms(template: dict[str, Any]) -> frozenset[str]:
    forms: set[str] = set()
    forms.add(_normalize_heading_text(str(template["title"])))
    for a in template.get("aliases") or ():
        forms.add(_normalize_heading_text(str(a)))
    return frozenset(forms)


def key_to_normalized_forms() -> dict[str, frozenset[str]]:
    """Template keys in rule order; shared with Stage 8.2 section-order check."""
    return {str(tpl["key"]): _template_normalized_forms(tpl) for tpl in REQUIRED_SECTION_TEMPLATES}


def resolve_norm_to_required_key(norm: str, forms_by_key: dict[str, frozenset[str]]) -> str | None:
    """First template-order key whose normalized forms contain ``norm``."""
    for key in REQUIRED_SECTIONS:
        if norm in forms_by_key[key]:
            return key
    return None


def check_required_sections_presence(structure: dict[str, Any]) -> dict[str, Any]:
    """Compare enriched ``structure`` flat ``sections`` to ``REQUIRED_SECTION_TEMPLATES``.

    Returns ``{"required_sections_check": {"present": [...], "missing": [...]}}`` with
    stable section ``key`` strings in template order. Duplicate headings do not duplicate
    keys in ``present``.
    """
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    detected_norms: list[str] = []
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        t = sec.get("title")
        if t is None:
            continue
        detected_norms.append(_detected_title_normalized_for_match(str(t)))

    detected_set = frozenset(detected_norms)

    key_to_forms = key_to_normalized_forms()

    found_keys: set[str] = set()
    for key, forms in key_to_forms.items():
        if forms & detected_set:
            found_keys.add(key)

    present = [k for k in REQUIRED_SECTIONS if k in found_keys]
    missing = [k for k in REQUIRED_SECTIONS if k not in found_keys]

    return {"required_sections_check": {"present": present, "missing": missing}}
