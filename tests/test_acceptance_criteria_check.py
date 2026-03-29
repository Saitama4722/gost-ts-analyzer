"""Tests for Stage 9.5 acceptance-criteria / verifiability presence check."""

from backend.app.checks.acceptance_criteria_check import check_document_acceptance_criteria


def _ac(structure: dict, full_text: str) -> dict:
    return check_document_acceptance_criteria(structure, full_text)["acceptance_criteria_check"]


def test_absent_when_empty():
    out = _ac({"sections": []}, "")
    assert out["is_present"] is False
    assert out["match_type"] is None
    assert out["matched_signal"] is None
    assert out["source"] is None


def test_absent_when_no_signal():
    out = _ac(
        {"sections": [{"title": "Введение", "start_block": 0}]},
        "Общие сведения. Система должна работать быстро.",
    )
    assert out["is_present"] is False


def test_functional_heading_does_not_satisfy_acceptance():
    """Stage 9.3 functional-requirements headings must not count as acceptance criteria."""
    out = _ac(
        {
            "sections": [
                {"title": "Функциональные требования", "start_block": 0},
            ]
        },
        "",
    )
    assert out["is_present"] is False


def test_section_title_match():
    structure = {"sections": [{"title": "Критерии приёмки", "start_block": 0}]}
    out = _ac(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Критерии приёмки"
    assert out["source"] == {"section_title": "Критерии приёмки"}


def test_section_title_numbered_prefix():
    structure = {"sections": [{"title": "6. Методика проверки", "start_block": 0}]}
    out = _ac(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Методика проверки"


def test_section_title_uppercase():
    structure = {"sections": [{"title": "ПРИЁМОЧНЫЕ ИСПЫТАНИЯ", "start_block": 0}]}
    out = _ac(structure, "дополнительный текст")
    assert out["is_present"] is True
    assert out["matched_signal"] == "Приёмочные испытания"


def test_text_phrase_when_no_heading():
    structure = {"sections": []}
    text = (
        "Вводный абзац.\n\n"
        "Требование считается выполненным, если все тесты пройдены успешно."
    )
    out = _ac(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
    assert out["matched_signal"] == "требование считается выполненным, если"
    assert "text_excerpt" in (out["source"] or {})
    assert "требование считается выполненным, если" in out["source"]["text_excerpt"]


def test_text_phrase_whitespace_normalized():
    structure = {"sections": []}
    text = "Соответствие   проверяется\nпо результатам испытаний."
    out = _ac(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_section_wins_over_body_phrase():
    structure = {
        "sections": [
            {"title": "Порядок приёмки", "start_block": 0},
        ]
    }
    text = "Требование считается выполненным, если модуль сдан."
    out = _ac(structure, text)
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Порядок приёмки"


def test_first_section_signal_wins_on_duplicates():
    structure = {
        "sections": [
            {"title": "Критерии приёмки", "start_block": 0},
            {"title": "Методика проверки", "start_block": 1},
        ]
    }
    out = _ac(structure, "")
    assert out["matched_signal"] == "Критерии приёмки"


def test_invalid_sections_list_treated_as_empty():
    out = check_document_acceptance_criteria(
        {"sections": "bad"},
        "Приёмка осуществляется по акту сдачи-приёмки.",
    )["acceptance_criteria_check"]
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_generic_check_word_alone_not_enough():
    """Bare «проверка» without acceptance/verifiability wording must not match."""
    out = _ac({"sections": []}, "Проверка кода выполняется ежедневно.")
    assert out["is_present"] is False
