"""Config shape for Stage 7.2 required-section template (no validation logic)."""

from __future__ import annotations

from backend.app.rules import (
    REQUIRED_SECTIONS,
    REQUIRED_SECTION_TEMPLATES,
    SECTION_ORDER_EXPECTED,
)


def test_required_section_templates_non_empty_and_consistent() -> None:
    assert len(REQUIRED_SECTION_TEMPLATES) > 0
    keys: list[str] = []
    for item in REQUIRED_SECTION_TEMPLATES:
        assert "key" in item and "title" in item and "aliases" in item
        assert isinstance(item["key"], str) and item["key"]
        assert isinstance(item["title"], str) and item["title"]
        assert isinstance(item["aliases"], tuple) and len(item["aliases"]) > 0
        for alias in item["aliases"]:
            assert isinstance(alias, str) and alias
        keys.append(item["key"])
    assert len(keys) == len(set(keys)), "template keys must be unique"
    assert REQUIRED_SECTIONS == tuple(keys)
    assert SECTION_ORDER_EXPECTED == tuple(keys)
