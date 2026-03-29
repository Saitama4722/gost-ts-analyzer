"""Tests for Stage 9.3 functional-requirements presence check."""

from backend.app.checks.functional_requirements_check import check_document_functional_requirements


def _fr(structure: dict, full_text: str) -> dict:
    return check_document_functional_requirements(structure, full_text)["functional_requirements_check"]


def test_absent_when_empty():
    out = _fr({"sections": []}, "")
    assert out["is_present"] is False
    assert out["match_type"] is None
    assert out["matched_signal"] is None
    assert out["source"] is None


def test_absent_when_no_signal():
    out = _fr(
        {"sections": [{"title": "Введение", "start_block": 0}]},
        "Общие сведения. Требования к оформлению документации.",
    )
    assert out["is_present"] is False


def test_purpose_and_scope_headings_do_not_satisfy_functional():
    """Stages 9.1 / 9.2 signals must not count as functional requirements."""
    out = _fr(
        {
            "sections": [
                {"title": "Назначение документа", "start_block": 0},
                {"title": "Область применения", "start_block": 1},
            ]
        },
        "",
    )
    assert out["is_present"] is False


def test_section_title_match():
    structure = {"sections": [{"title": "Функциональные требования", "start_block": 0}]}
    out = _fr(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Функциональные требования"
    assert out["source"] == {"section_title": "Функциональные требования"}


def test_section_title_numbered_prefix():
    structure = {"sections": [{"title": "4. Требования к функциям", "start_block": 0}]}
    out = _fr(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Требования к функциям"


def test_section_title_uppercase():
    structure = {"sections": [{"title": "ФУНКЦИИ СИСТЕМЫ", "start_block": 0}]}
    out = _fr(structure, "дополнительный текст")
    assert out["is_present"] is True
    assert out["matched_signal"] == "Функции системы"


def test_text_phrase_when_no_heading():
    structure = {"sections": []}
    text = "Вводный абзац.\n\nСистема должна обеспечивать учёт заявок и отчётность."
    out = _fr(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
    assert out["matched_signal"] == "система должна обеспечивать"
    assert "text_excerpt" in (out["source"] or {})
    assert "система должна обеспечивать" in out["source"]["text_excerpt"]


def test_text_phrase_whitespace_normalized():
    structure = {"sections": []}
    text = "Программа   должна   обеспечивать\nинтеграцию с внешними системами."
    out = _fr(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_section_wins_over_body_phrase():
    structure = {
        "sections": [
            {"title": "Функции программного средства", "start_block": 0},
        ]
    }
    text = "Система должна обеспечивать резервное копирование."
    out = _fr(structure, text)
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Функции программного средства"


def test_first_section_signal_wins_on_duplicates():
    structure = {
        "sections": [
            {"title": "Функциональные требования", "start_block": 0},
            {"title": "Требования к функциям", "start_block": 1},
        ]
    }
    out = _fr(structure, "")
    assert out["matched_signal"] == "Функциональные требования"


def test_invalid_sections_list_treated_as_empty():
    out = check_document_functional_requirements(
        {"sections": "bad"},
        "Функциональные требования включают регистрацию пользователей.",
    )["functional_requirements_check"]
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
