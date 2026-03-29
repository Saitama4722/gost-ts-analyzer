"""Tests for Stage 9.1 document purpose presence check."""

from backend.app.checks.purpose_check import check_document_purpose


def _pc(structure: dict, full_text: str) -> dict:
    return check_document_purpose(structure, full_text)["purpose_check"]


def test_absent_when_empty():
    out = _pc({"sections": []}, "")
    assert out["is_present"] is False
    assert out["match_type"] is None
    assert out["matched_signal"] is None
    assert out["source"] is None


def test_absent_when_no_signal():
    out = _pc({"sections": [{"title": "Введение", "start_block": 0}]}, "Общие сведения о системе.")
    assert out["is_present"] is False


def test_section_title_match():
    structure = {"sections": [{"title": "Назначение", "start_block": 0}]}
    out = _pc(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Назначение"
    assert out["source"] == {"section_title": "Назначение"}


def test_section_title_numbered_prefix():
    structure = {"sections": [{"title": "1. Назначение документа", "start_block": 0}]}
    out = _pc(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Назначение документа"


def test_section_title_uppercase():
    structure = {"sections": [{"title": "ЦЕЛЬ", "start_block": 0}]}
    out = _pc(structure, "дополнительный текст")
    assert out["is_present"] is True
    assert out["matched_signal"] == "Цель"


def test_text_phrase_when_no_heading():
    structure = {"sections": []}
    text = "Вводная часть.\n\nЦелью документа является описание требований к системе."
    out = _pc(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
    assert out["matched_signal"] == "Целью документа является"
    assert "text_excerpt" in (out["source"] or {})
    assert "целью документа является" in out["source"]["text_excerpt"]


def test_text_phrase_whitespace_normalized():
    structure = {"sections": []}
    text = "Документ   предназначен\nдля сопровождения разработки."
    out = _pc(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_section_wins_over_body_phrase():
    structure = {
        "sections": [
            {"title": "Цель", "start_block": 0},
        ]
    }
    text = "Назначение документа — другое."
    out = _pc(structure, text)
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Цель"


def test_first_section_signal_wins_on_duplicates():
    structure = {
        "sections": [
            {"title": "Цель документа", "start_block": 0},
            {"title": "Назначение", "start_block": 1},
        ]
    }
    out = _pc(structure, "")
    assert out["matched_signal"] == "Цель документа"


def test_invalid_sections_list_treated_as_empty():
    out = check_document_purpose({"sections": "bad"}, "Назначение документа — текст.")[
        "purpose_check"
    ]
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
