"""Structure checks for Stage 7.3 vague-phrase configuration (no detection logic)."""

from __future__ import annotations

from backend.app.rules import FORBIDDEN_VAGUE_PHRASES


def test_forbidden_vague_phrases_not_empty() -> None:
    assert len(FORBIDDEN_VAGUE_PHRASES) > 0


def test_each_entry_has_required_fields() -> None:
    required = {"phrase", "type", "description"}
    for item in FORBIDDEN_VAGUE_PHRASES:
        assert set(item.keys()) == required
        assert isinstance(item["phrase"], str) and item["phrase"].strip()
        assert isinstance(item["type"], str) and item["type"].strip()
        assert isinstance(item["description"], str) and item["description"].strip()


def test_phrases_are_unique() -> None:
    phrases = [entry["phrase"] for entry in FORBIDDEN_VAGUE_PHRASES]
    assert len(phrases) == len(set(phrases))
