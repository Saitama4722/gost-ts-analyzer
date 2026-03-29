"""Shared helpers for deterministic phrase/title matching in content checks (9.x)."""

from __future__ import annotations


def collapse_ws_casefold(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def phrase_search_key(phrase: str) -> str:
    return collapse_ws_casefold(phrase)
