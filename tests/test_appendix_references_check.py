"""Tests for Stage 11.3 — appendix mentions vs heading declarations."""

from __future__ import annotations

from backend.app.checks.appendix_references_check import check_document_appendix_references


def _ar(blocks: list[str]) -> dict:
    return check_document_appendix_references(blocks)["appendix_references_check"]


def test_empty_and_whitespace_blocks() -> None:
    out = _ar([])
    assert out["has_issues"] is False
    assert out["mentioned_labels"] == []
    assert out["declared_labels"] == []
    assert out["missing_declarations"] == []
    assert out["unreferenced_appendices"] == []
    assert out["duplicate_declarations"] == []
    assert out["mentions"] == []
    assert out["declarations"] == []
    out2 = _ar(["", "  \n  "])
    assert out2["has_issues"] is False


def test_mention_and_declaration_consistent() -> None:
    blocks = [
        "Подробные расчёты приведены в приложении А.\nПриложение А — Расчётные данные.",
    ]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["А"]
    assert out["declared_labels"] == ["А"]
    assert out["missing_declarations"] == []
    assert out["unreferenced_appendices"] == []
    assert out["duplicate_declarations"] == []
    assert out["has_issues"] is False


def test_heading_line_not_counted_as_mention() -> None:
    blocks = ["Приложение Б — Перечень сокращений."]
    out = _ar(blocks)
    assert out["declared_labels"] == ["Б"]
    assert out["mentioned_labels"] == []
    assert out["unreferenced_appendices"] == ["Б"]
    assert out["missing_declarations"] == []
    assert out["has_issues"] is True


def test_heading_with_period_after_label() -> None:
    blocks = ["В приложении В указано.\nПриложение В. Справочные таблицы."]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["В"]
    assert out["declared_labels"] == ["В"]
    assert out["has_issues"] is False


def test_missing_declaration_for_mention() -> None:
    blocks = ["См. приложение Г для деталей."]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["Г"]
    assert out["declared_labels"] == []
    assert out["missing_declarations"] == ["Г"]
    assert out["has_issues"] is True


def test_unreferenced_appendix() -> None:
    blocks = ["Приложение Д — Схема.", "Текст без ссылок на приложения."]
    out = _ar(blocks)
    assert out["declared_labels"] == ["Д"]
    assert out["mentioned_labels"] == []
    assert out["unreferenced_appendices"] == ["Д"]
    assert out["has_issues"] is True


def test_duplicate_declarations() -> None:
    blocks = [
        "Приложение Е — Первое.\nПриложение Е — Дубликат.",
    ]
    out = _ar(blocks)
    assert out["declared_labels"] == ["Е"]
    assert out["duplicate_declarations"] == ["Е"]
    assert out["has_issues"] is True


def test_repeated_mentions_same_label() -> None:
    blocks = [
        "Приложение Ж — Данные.\nСм. приложение Ж и снова в приложении Ж.",
    ]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["Ж"]
    assert len(out["mentions"]) == 2
    assert out["has_issues"] is False


def test_grammatical_cases() -> None:
    blocks = [
        "Согласно приложению З.\nДанные приложения З.\nПриложение З — Заголовок.",
    ]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["З"]
    assert out["declared_labels"] == ["З"]
    assert out["has_issues"] is False


def test_numeric_appendix() -> None:
    blocks = ["См. приложение 2.\nПриложение 2 — Описание."]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["2"]
    assert out["declared_labels"] == ["2"]
    assert out["has_issues"] is False


def test_numeric_appendix_gaps_reported() -> None:
    blocks = ["Приложение 1 — А.\nПриложение 5 — Б."]
    out = _ar(blocks)
    assert out["declared_labels"] == ["1", "5"]
    assert out["numeric_appendix_gaps"] == [2, 3, 4]
    assert out["unreferenced_appendices"] == ["1", "5"]
    assert out["has_issues"] is True


def test_cyrillic_letter_sequence_gaps_reported() -> None:
    blocks = ["Приложение А — .\nПриложение В — ."]
    out = _ar(blocks)
    assert out["cyrillic_letter_sequence_gaps"] == ["Б"]
    assert out["unreferenced_appendices"] == ["А", "В"]
    assert out["has_issues"] is True


def test_does_not_treat_attachment_phrase_as_appendix() -> None:
    blocks = [
        "Приложение к настоящему договору составляет его часть.",
        "Текст про приложения к договору и условия поставки.",
    ]
    out = _ar(blocks)
    assert out["mentioned_labels"] == []
    assert out["declared_labels"] == []


def test_does_not_match_bare_letter_without_keyword() -> None:
    blocks = ["Точка А на схеме соответствует входу."]
    out = _ar(blocks)
    assert out["mentioned_labels"] == []
    assert out["declared_labels"] == []


def test_case_insensitive() -> None:
    blocks = ["приложение и — подпись.\nСм. ПРИЛОЖЕНИЕ И."]
    out = _ar(blocks)
    assert out["declared_labels"] == ["И"]
    assert out["mentioned_labels"] == ["И"]
    assert out["has_issues"] is False


def test_user_example_structure() -> None:
    """Mentions {А,Б,Г}, declarations {А,Б,В} → missing Г, unreferenced В."""
    blocks = [
        "Приложение А — A.\nПриложение Б — B.\nПриложение В — C.",
        "Данные в приложении А и приложении Б согласованы. См. также приложение Г.",
    ]
    out = _ar(blocks)
    assert out["mentioned_labels"] == ["А", "Б", "Г"]
    assert out["declared_labels"] == ["А", "Б", "В"]
    assert out["missing_declarations"] == ["Г"]
    assert out["unreferenced_appendices"] == ["В"]
    assert out["duplicate_declarations"] == []
    assert out["has_issues"] is True
