"""Tests for Stage 10.3 — numerical characteristics in obligation-style fragments."""

from __future__ import annotations

from backend.app.checks.numerical_characteristics_check import check_document_numerical_characteristics


def _nc(structure: dict, full_text: str) -> dict:
    return check_document_numerical_characteristics(structure, full_text)["numerical_characteristics_check"]


def test_empty_and_whitespace() -> None:
    for text in ("", "  \n\t"):
        out = _nc({"sections": []}, text)
        assert out["has_numeric_findings"] is False
        assert out["items"] == []
        assert out["item_count"] == 0


def test_no_obligation_no_items() -> None:
    out = _nc({"sections": []}, "Система обрабатывает запросы и журналирует события.")
    assert out["item_count"] == 0


def test_negative_examples_no_numeric_signals() -> None:
    examples = (
        "Система должна быть удобной в использовании.",
        "Приложение должно быстро загружаться.",
        "Интерфейс должен быть понятным.",
        "Сервис должен обеспечивать надежную работу.",
    )
    for sentence in examples:
        out = _nc({"sections": []}, sentence)
        assert out["item_count"] == 1, sentence
        item = out["items"][0]
        assert item["text"] == sentence.strip()
        assert item["has_numeric_characteristics"] is False
        assert item["matched_signals"] == []
    assert _nc({"sections": []}, " ".join(examples))["has_numeric_findings"] is False


def test_positive_user_examples() -> None:
    cases: tuple[tuple[str, list[str]], ...] = (
        (
            "Система должна обрабатывать не менее 100 запросов в секунду.",
            ["number", "rate", "threshold"],
        ),
        (
            "Время отклика должно быть не более 2 с.",
            ["duration", "number", "threshold", "unit"],
        ),
        (
            "Доступность сервиса должна составлять не менее 99,5% в месяц.",
            ["number", "percentage", "threshold", "unit"],
        ),
        (
            "Ошибка обработки должна отображаться пользователю в течение 3 секунд.",
            ["duration", "number"],
        ),
        (
            "Температура должна поддерживаться в диапазоне от 18 до 24 °C.",
            ["number", "range", "threshold", "unit"],
        ),
    )
    for sentence, expected_sub in cases:
        out = _nc({"sections": []}, sentence)
        assert out["item_count"] == 1, sentence
        item = out["items"][0]
        assert item["has_numeric_characteristics"] is True, sentence
        for sig in expected_sub:
            assert sig in item["matched_signals"], (sentence, item["matched_signals"])


def test_comparison_operators() -> None:
    out = _nc({"sections": []}, "Задержка передачи должна быть p <= 0.05 с для 95% случаев.")
    assert out["item_count"] == 1
    sigs = out["items"][0]["matched_signals"]
    assert "comparison" in sigs
    assert "number" in sigs


def test_range_dash_interval() -> None:
    out = _nc({"sections": []}, "Мощность должна находиться в интервале 10–20 кВт.")
    assert out["items"][0]["has_numeric_characteristics"] is True
    assert "range" in out["items"][0]["matched_signals"]


def test_duplicate_fragments_deduped() -> None:
    text = (
        "Система должна быть удобной в использовании. "
        "Система должна быть удобной в использовании."
    )
    out = _nc({"sections": []}, text)
    assert out["item_count"] == 1


def test_section_title_and_fragment_index() -> None:
    structure = {
        "sections": [
            {
                "title": "4. Требования",
                "content_text": "Модуль должен выдерживать не менее 50 одновременных сессий.",
            }
        ]
    }
    out = _nc(structure, "")
    assert out["item_count"] == 1
    item = out["items"][0]
    assert item["section_title"] == "4. Требования"
    assert item["fragment_index"] == 0
    assert item["has_numeric_characteristics"] is True


def test_short_fragment_skipped() -> None:
    out = _nc({"sections": []}, "Узел должен быть стабилен.")
    assert out["item_count"] == 0


def test_fallback_to_full_text_when_no_section_body() -> None:
    structure = {"sections": [{"title": "Пустой", "content_text": ""}]}
    full = "Компонент должен отвечать не дольше 5 мс."
    out = _nc(structure, full)
    assert out["item_count"] == 1
    assert "duration" in out["items"][0]["matched_signals"]
    assert "threshold" in out["items"][0]["matched_signals"]
