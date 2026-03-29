"""Tests for Stage 11.2 — table mentions vs caption declarations."""

from __future__ import annotations

from backend.app.checks.table_references_check import check_document_table_references


def _tr(blocks: list[str]) -> dict:
    return check_document_table_references(blocks)["table_references_check"]


def test_empty_and_whitespace_blocks() -> None:
    out = _tr([])
    assert out["has_issues"] is False
    assert out["mentioned_numbers"] == []
    assert out["declared_numbers"] == []
    assert out["missing_declarations"] == []
    assert out["unreferenced_tables"] == []
    assert out["duplicate_declarations"] == []
    assert out["mentions"] == []
    assert out["declarations"] == []
    out2 = _tr(["", "  \n  "])
    assert out2["has_issues"] is False


def test_mention_and_declaration_consistent() -> None:
    blocks = [
        "В таблице 1 приведены результаты.\nТаблица 1 — Результаты испытаний.",
    ]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == [1]
    assert out["declared_numbers"] == [1]
    assert out["missing_declarations"] == []
    assert out["unreferenced_tables"] == []
    assert out["duplicate_declarations"] == []
    assert out["has_issues"] is False


def test_caption_line_not_counted_as_mention() -> None:
    blocks = ["Таблица 2 — Перечень параметров."]
    out = _tr(blocks)
    assert out["declared_numbers"] == [2]
    assert out["mentioned_numbers"] == []
    assert out["unreferenced_tables"] == [2]
    assert out["missing_declarations"] == []
    assert out["has_issues"] is True


def test_missing_declaration_for_mention() -> None:
    blocks = ["См. таблицу 3 и табл. 4."]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == [3, 4]
    assert out["declared_numbers"] == []
    assert out["missing_declarations"] == [3, 4]
    assert out["has_issues"] is True


def test_unreferenced_table() -> None:
    blocks = ["Табл. 5. Сводные данные.", "Текст без ссылок на таблицы."]
    out = _tr(blocks)
    assert out["declared_numbers"] == [5]
    assert out["mentioned_numbers"] == []
    assert out["unreferenced_tables"] == [5]
    assert out["has_issues"] is True


def test_duplicate_declarations() -> None:
    blocks = [
        "Таблица 2 — Первая.\nТаблица 2 — Дубликат.",
    ]
    out = _tr(blocks)
    assert out["declared_numbers"] == [2]
    assert out["duplicate_declarations"] == [2]
    assert out["has_issues"] is True


def test_repeated_mentions_same_number() -> None:
    blocks = [
        "Таблица 1 — А.\nСм. таблицу 1 и снова табл. 1.",
    ]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == [1]
    assert len(out["mentions"]) == 2
    assert out["has_issues"] is False


def test_grammatical_cases_and_tabl_abbreviation() -> None:
    blocks = [
        "В таблице 7 указаны нормы.\nПо таблице 7.\nТаблица 7 — Нормы.",
    ]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == [7]
    assert out["declared_numbers"] == [7]
    assert out["has_issues"] is False


def test_caption_numbering_gaps_reported() -> None:
    blocks = ["Таблица 1 — А.\nТаблица 5 — Б."]
    out = _tr(blocks)
    assert out["declared_numbers"] == [1, 5]
    assert out["caption_numbering_gaps"] == [2, 3, 4]
    assert out["unreferenced_tables"] == [1, 5]
    assert out["has_issues"] is True


def test_does_not_match_bare_numbers_without_table_keyword() -> None:
    blocks = ["Раздел 2 содержит три подпункта."]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == []
    assert out["declarations"] == []


def test_case_insensitive() -> None:
    blocks = ["таблица 1 — подпись.\nСм. ТАБЛ. 1."]
    out = _tr(blocks)
    assert out["declared_numbers"] == [1]
    assert out["mentioned_numbers"] == [1]
    assert out["has_issues"] is False


def test_user_example_structure() -> None:
    """Mentions {1,2,4}, declarations {1,2,3} → missing 4, unreferenced 3."""
    blocks = [
        "Таблица 1 — A.\nТаблица 2 — B.\nТаблица 3 — C.",
        "Данные в таблице 1 и табл. 2 согласованы. См. также таблицу 4.",
    ]
    out = _tr(blocks)
    assert out["mentioned_numbers"] == [1, 2, 4]
    assert out["declared_numbers"] == [1, 2, 3]
    assert out["missing_declarations"] == [4]
    assert out["unreferenced_tables"] == [3]
    assert out["duplicate_declarations"] == []
    assert out["has_issues"] is True
