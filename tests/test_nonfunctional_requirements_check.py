"""Tests for Stage 9.4 non-functional-requirements presence check."""

from backend.app.checks.nonfunctional_requirements_check import check_document_nonfunctional_requirements


def _nfr(structure: dict, full_text: str) -> dict:
    return check_document_nonfunctional_requirements(structure, full_text)["nonfunctional_requirements_check"]


def test_absent_when_empty():
    out = _nfr({"sections": []}, "")
    assert out["is_present"] is False
    assert out["match_type"] is None
    assert out["matched_signal"] is None
    assert out["source"] is None


def test_absent_when_no_signal():
    out = _nfr(
        {"sections": [{"title": "Введение", "start_block": 0}]},
        "Общие сведения. Функции системы и пользовательские сценарии.",
    )
    assert out["is_present"] is False


def test_functional_heading_does_not_satisfy_nonfunctional():
    """Stage 9.3 functional-requirements headings must not count as non-functional."""
    out = _nfr(
        {
            "sections": [
                {"title": "Функциональные требования", "start_block": 0},
            ]
        },
        "",
    )
    assert out["is_present"] is False


def test_section_title_match():
    structure = {"sections": [{"title": "Требования к надёжности", "start_block": 0}]}
    out = _nfr(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Требования к надёжности"
    assert out["source"] == {"section_title": "Требования к надёжности"}


def test_section_title_numbered_prefix():
    structure = {"sections": [{"title": "5. Нефункциональные требования", "start_block": 0}]}
    out = _nfr(structure, "")
    assert out["is_present"] is True
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Нефункциональные требования"


def test_section_title_uppercase():
    structure = {"sections": [{"title": "ТРЕБОВАНИЯ К БЕЗОПАСНОСТИ", "start_block": 0}]}
    out = _nfr(structure, "дополнительный текст")
    assert out["is_present"] is True
    assert out["matched_signal"] == "Требования к безопасности"


def test_text_phrase_when_no_heading():
    structure = {"sections": []}
    text = (
        "Вводный абзац.\n\n"
        "Время отклика не должно превышать 2 секунд при нормальной нагрузке."
    )
    out = _nfr(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
    assert out["matched_signal"] == "время отклика не должно превышать"
    assert "text_excerpt" in (out["source"] or {})
    assert "время отклика не должно превышать" in out["source"]["text_excerpt"]


def test_text_phrase_whitespace_normalized():
    structure = {"sections": []}
    text = "Доступность   системы   должна\nсоставлять не менее 99,9%."
    out = _nfr(structure, text)
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"


def test_section_wins_over_body_phrase():
    structure = {
        "sections": [
            {"title": "Требования к производительности", "start_block": 0},
        ]
    }
    text = "Время отклика не должно превышать одной секунды."
    out = _nfr(structure, text)
    assert out["match_type"] == "section_title"
    assert out["matched_signal"] == "Требования к производительности"


def test_first_section_signal_wins_on_duplicates():
    structure = {
        "sections": [
            {"title": "Нефункциональные требования", "start_block": 0},
            {"title": "Требования к безопасности", "start_block": 1},
        ]
    }
    out = _nfr(structure, "")
    assert out["matched_signal"] == "Нефункциональные требования"


def test_invalid_sections_list_treated_as_empty():
    out = check_document_nonfunctional_requirements(
        {"sections": "bad"},
        "Требования к надёжности включают резервирование узлов.",
    )["nonfunctional_requirements_check"]
    assert out["is_present"] is True
    assert out["match_type"] == "text_phrase"
