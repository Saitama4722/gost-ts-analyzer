"""Tests for Stage 9.2 document scope / application-area presence check."""

from backend.app.checks.scope_check import check_document_scope


def _sc(structure: dict, full_text: str) -> dict:
    return check_document_scope(structure, full_text)["scope_check"]


def test_absent_when_empty():
    out = _sc({"sections": []}, "")
    assert out["is_present"] is False
    assert out["match_type"] is None
    assert out["matched_signal"] is None
    assert out["source"] is None


def test_absent_when_no_signal():
    out = _sc({"sections": [{"title": "Введение", "start_block": 0}]}, "Общие сведения о системе.")
    assert out["is_present"] is False


def test_purpose_heading_does_not_satisfy_scope():
    """Stage 9.1 purpose signals must not count as scope."""
    out = _sc({"sections": [{"title": "Назначение документа", "start_block": 0}]}, "")
    assert out["is_present"] is False


def test_section_title_match():
    structure = {"sections": [{"title": "Область применения", "start_block": 0}]}
    out = _sc(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Область применения"
    assert out["source"] == {"section_title": "Область применения"}


def test_section_title_numbered_prefix():
    structure = {"sections": [{"title": "3. Сфера применения", "start_block": 0}]}
    out = _sc(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Сфера применения"


def test_section_title_uppercase():
    structure = {"sections": [{"title": "ОБЛАСТЬ ДЕЙСТВИЯ", "start_block": 0}]}
    out = _sc(structure, "дополнительный текст")
    assert out["is_present"] is True
    assert out["matched_signal"] == "Область действия"


def test_text_phrase_when_no_heading():
    structure = {"sections": []}
    text = (
        "Вводный абзац.\n\nНастоящий документ распространяется на подсистемы учёта и отчётности."
    )
    out = _sc(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
    assert out["matched_signal"] == "Настоящий документ распространяется на"
    assert "text_excerpt" in (out["source"] or {})
    assert "настоящий документ распространяется на" in out["source"]["text_excerpt"]


def test_text_phrase_whitespace_normalized():
    structure = {"sections": []}
    text = "Документ   применяется\nк объектам автоматизации."
    out = _sc(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_section_wins_over_body_phrase():
    structure = {
        "sections": [
            {"title": "Область использования", "start_block": 0},
        ]
    }
    text = "Сфера применения ограничена договором."
    out = _sc(structure, text)
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Область использования"


def test_first_section_signal_wins_on_duplicates():
    structure = {
        "sections": [
            {"title": "Область применения", "start_block": 0},
            {"title": "Сфера применения", "start_block": 1},
        ]
    }
    out = _sc(structure, "")
    assert out["matched_signal"] == "Область применения"


def test_invalid_sections_list_treated_as_empty():
    out = check_document_scope(
        {"sections": "bad"},
        "Область применения документа — описание границ.",
    )["scope_check"]
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
