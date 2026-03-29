"""Tests for Stage 11.1 — figure mentions vs caption declarations."""

from __future__ import annotations

from backend.app.checks.figure_references_check import check_document_figure_references


def _fr(blocks: list[str]) -> dict:
    return check_document_figure_references(blocks)["figure_references_check"]


def test_empty_and_whitespace_blocks() -> None:
    out = _fr([])
    assert out["has_issues"] is False
    assert out["mentioned_numbers"] == []
    assert out["declared_numbers"] == []
    assert out["missing_declarations"] == []
    assert out["unreferenced_figures"] == []
    assert out["duplicate_declarations"] == []
    assert out["mentions"] == []
    assert out["declarations"] == []
    out2 = _fr(["", "  \n  "])
    assert out2["has_issues"] is False


def test_mention_and_declaration_consistent() -> None:
    blocks = [
        "На рисунке 1 показана схема.\nРисунок 1 — Схема взаимодействия модулей.",
    ]
    out = _fr(blocks)
    assert out["mentioned_numbers"] == [1]
    assert out["declared_numbers"] == [1]
    assert out["missing_declarations"] == []
    assert out["unreferenced_figures"] == []
    assert out["duplicate_declarations"] == []
    assert out["has_issues"] is False


def test_caption_line_not_counted_as_mention() -> None:
    blocks = ["Рисунок 2 — Подпись к рисунку."]
    out = _fr(blocks)
    assert out["declared_numbers"] == [2]
    assert out["mentioned_numbers"] == []
    assert out["unreferenced_figures"] == [2]
    assert out["missing_declarations"] == []
    assert out["has_issues"] is True


def test_missing_declaration_for_mention() -> None:
    blocks = ["См. рисунок 3 и рис. 4 для деталей."]
    out = _fr(blocks)
    assert out["mentioned_numbers"] == [3, 4]
    assert out["declared_numbers"] == []
    assert out["missing_declarations"] == [3, 4]
    assert out["has_issues"] is True


def test_unreferenced_figure() -> None:
    blocks = ["Рис. 5. Общая схема.", "Текст без ссылок на рисунки."]
    out = _fr(blocks)
    assert out["declared_numbers"] == [5]
    assert out["mentioned_numbers"] == []
    assert out["unreferenced_figures"] == [5]
    assert out["has_issues"] is True


def test_duplicate_declarations() -> None:
    blocks = [
        "Рисунок 2 — Первый.\nРисунок 2 — Дубликат.",
    ]
    out = _fr(blocks)
    assert out["declared_numbers"] == [2]
    assert out["duplicate_declarations"] == [2]
    assert out["has_issues"] is True


def test_repeated_mentions_same_number() -> None:
    blocks = [
        "Рисунок 1 — А.\nСм. рисунок 1 и снова рис. 1.",
    ]
    out = _fr(blocks)
    assert out["mentioned_numbers"] == [1]
    assert len(out["mentions"]) == 2
    assert out["has_issues"] is False


def test_grammatical_cases_and_ris_abbreviation() -> None:
    blocks = [
        "На рисунке 7 видно узел.\nПо рисунку 7.\nРисунок 7 — Узел.",
    ]
    out = _fr(blocks)
    assert out["mentioned_numbers"] == [7]
    assert out["declared_numbers"] == [7]
    assert out["has_issues"] is False


def test_caption_numbering_gaps_reported() -> None:
    blocks = ["Рисунок 1 — А.\nРисунок 5 — Б."]
    out = _fr(blocks)
    assert out["declared_numbers"] == [1, 5]
    assert out["caption_numbering_gaps"] == [2, 3, 4]
    assert out["has_issues"] is True  # unreferenced optional: 1 and 5 not mentioned in text
    assert out["unreferenced_figures"] == [1, 5]


def test_does_not_match_bare_version_numbers() -> None:
    blocks = ["Версия 2 системы должна поддерживать обновления."]
    out = _fr(blocks)
    assert out["mentioned_numbers"] == []
    assert out["declarations"] == []


def test_case_insensitive() -> None:
    blocks = ["рисунок 1 — низ.\nСм. РИС. 1."]
    out = _fr(blocks)
    assert out["declared_numbers"] == [1]
    assert out["mentioned_numbers"] == [1]
    assert out["has_issues"] is False
