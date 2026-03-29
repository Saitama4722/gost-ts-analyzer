"""Tests for Stage 7.4 glossary configuration (shape only; no matching logic)."""

from backend.app.rules import GLOSSARY_CANONICAL_TERMS


def test_glossary_not_empty() -> None:
    assert len(GLOSSARY_CANONICAL_TERMS) > 0


def test_glossary_entries_shape_and_uniqueness() -> None:
    keys: set[str] = set()
    required = frozenset({"key", "canonical", "aliases"})

    for item in GLOSSARY_CANONICAL_TERMS:
        assert set(item.keys()) == required
        assert item["key"]
        assert item["canonical"]
        aliases = item["aliases"]
        assert isinstance(aliases, tuple)
        assert len(aliases) > 0
        assert item["canonical"] in aliases
        assert len(aliases) == len(set(aliases)), f"duplicate alias in {item['key']}"
        keys.add(item["key"])

    assert len(keys) == len(GLOSSARY_CANONICAL_TERMS)
