"""Tests for Stage 10.4 — measurement units and number–unit linkage."""

from __future__ import annotations

from backend.app.checks.measurement_units_check import check_document_measurement_units


def _mu(structure: dict, full_text: str) -> dict:
    return check_document_measurement_units(structure, full_text)["measurement_units_check"]


def test_empty_and_whitespace() -> None:
    for text in ("", "  \n\t"):
        out = _mu({"sections": []}, text)
        assert out["has_findings"] is False
        assert out["items"] == []
        assert out["item_count"] == 0


def test_no_obligation_no_items() -> None:
    out = _mu({"sections": []}, "Система обрабатывает запросы и журналирует события.")
    assert out["item_count"] == 0


def test_linked_examples_from_spec() -> None:
    cases = (
        "Время отклика должно быть не более 2 с.",
        "Доступность сервиса должна составлять не менее 99,5%.",
        "Система должна обрабатывать не менее 100 запросов в секунду.",
        "Температура должна поддерживаться в диапазоне от 18 до 24 °C.",
        "Объём памяти должен быть не менее 8 ГБ.",
    )
    for sentence in cases:
        out = _mu({"sections": []}, sentence)
        assert out["item_count"] == 1, sentence
        item = out["items"][0]
        assert item["has_numeric_value"] is True, sentence
        assert item["has_unit"] is True, sentence
        assert item["number_unit_linked"] is True, sentence
        assert item["reason"] == "числовое значение связано с единицей измерения", sentence
    assert _mu({"sections": []}, " ".join(cases))["has_findings"] is False


def test_numeric_without_unit() -> None:
    out = _mu({"sections": []}, "Время отклика должно быть не более 2.")
    assert out["item_count"] == 1
    item = out["items"][0]
    assert item["has_numeric_value"] is True
    assert item["has_unit"] is False
    assert item["number_unit_linked"] is False
    assert item["matched_units"] == []
    assert item["reason"] == "числовое значение обнаружено без единицы измерения"
    assert out["has_findings"] is True


def test_percentage_without_explicit_percent_sign() -> None:
    out = _mu({"sections": []}, "Доступность сервиса должна составлять не менее 99,5.")
    item = out["items"][0]
    assert item["has_numeric_value"] is True
    assert item["has_unit"] is False
    assert item["number_unit_linked"] is False
    assert out["has_findings"] is True


def test_unit_without_numeric() -> None:
    out = _mu({"sections": []}, "Интервал должен измеряться в секундах.")
    item = out["items"][0]
    assert item["has_numeric_value"] is False
    assert item["has_unit"] is True
    assert item["number_unit_linked"] is False
    assert "секундах" in item["matched_units"][0].casefold()
    assert item["reason"] == "упоминание единицы измерения без связанного числового значения"
    assert out["has_findings"] is True


def test_no_numeric_no_unit() -> None:
    out = _mu({"sections": []}, "Сервис должен обеспечивать скорость обработки.")
    item = out["items"][0]
    assert item["has_numeric_value"] is False
    assert item["has_unit"] is False
    assert item["number_unit_linked"] is False
    assert item["reason"] == "числовые значения и единицы измерения не обнаружены"
    assert out["has_findings"] is False


def test_compact_suffix_forms() -> None:
    out = _mu({"sections": []}, "Задержка должна быть не более 100мс при пиковой нагрузке.")
    item = out["items"][0]
    assert item["number_unit_linked"] is True
    assert item["has_unit"] is True

    out2 = _mu({"sections": []}, "Таймаут должен составлять 2с для критичных операций.")
    assert out2["items"][0]["number_unit_linked"] is True


def test_duplicate_fragments_deduped() -> None:
    text = (
        "Система должна обрабатывать не менее 10 запросов в секунду. "
        "Система должна обрабатывать не менее 10 запросов в секунду."
    )
    out = _mu({"sections": []}, text)
    assert out["item_count"] == 1


def test_section_title_and_fragment_index() -> None:
    structure = {
        "sections": [
            {
                "title": "4. Требования",
                "content_text": "Модуль должен выдерживать не более 500 мс ожидания.",
            }
        ]
    }
    out = _mu(structure, "")
    assert out["item_count"] == 1
    item = out["items"][0]
    assert item["section_title"] == "4. Требования"
    assert item["fragment_index"] == 0
    assert item["number_unit_linked"] is True
    assert "matched_signal_categories" in item


def test_short_fragment_skipped() -> None:
    out = _mu({"sections": []}, "Узел должен быть стабилен.")
    assert out["item_count"] == 0


def test_fallback_to_full_text_when_no_section_body() -> None:
    structure = {"sections": [{"title": "Пустой", "content_text": ""}]}
    full = "Компонент должен отвечать не дольше 5 мс."
    out = _mu(structure, full)
    assert out["item_count"] == 1
    assert out["items"][0]["number_unit_linked"] is True
