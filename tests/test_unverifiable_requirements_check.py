"""Tests for Stage 10.2 — unverifiable requirement-like phrasing (no measurable criteria)."""

from __future__ import annotations

from backend.app.checks.unverifiable_requirements_check import check_document_unverifiable_requirements


def _ur(structure: dict, full_text: str) -> dict:
    return check_document_unverifiable_requirements(structure, full_text)["unverifiable_requirements_check"]


def test_empty_and_whitespace() -> None:
    for text in ("", "  \n\t"):
        out = _ur({"sections": []}, text)
        assert out["has_findings"] is False
        assert out["items"] == []
        assert out["item_count"] == 0


def test_no_obligation_no_findings() -> None:
    out = _ur({"sections": []}, "Система обрабатывает запросы и журналирует события.")
    assert out["item_count"] == 0


def test_positive_user_examples() -> None:
    examples = (
        "Система должна быть удобной в использовании.",
        "Приложение должно быстро загружаться.",
        "Интерфейс должен быть понятным.",
        "Сервис должен обеспечивать надежную работу.",
    )
    for sentence in examples:
        out = _ur({"sections": []}, sentence)
        assert out["item_count"] == 1, sentence
        item = out["items"][0]
        assert item["text"] == sentence.strip()
        assert item["reason"]
        assert "obligation_marker" in item


def test_negative_user_examples_with_metrics() -> None:
    negatives = (
        "Система должна обрабатывать не менее 100 запросов в секунду.",
        "Время отклика должно быть не более 2 с.",
        "Доступность сервиса должна составлять не менее 99,5% в месяц.",
        "Ошибка обработки должна отображаться пользователю в течение 3 секунд.",
    )
    for sentence in negatives:
        out = _ur({"sections": []}, sentence)
        assert out["item_count"] == 0, sentence


def test_duplicate_fragments_deduped() -> None:
    text = (
        "Система должна быть удобной в использовании. "
        "Система должна быть удобной в использовании."
    )
    out = _ur({"sections": []}, text)
    assert out["item_count"] == 1


def test_section_title_metadata_when_using_content_text() -> None:
    structure = {
        "sections": [
            {
                "title": "4. Требования",
                "content_text": "Модуль должен быть расширяемым без доработки ядра.",
            }
        ]
    }
    out = _ur(structure, "")
    assert out["item_count"] == 1
    assert out["items"][0]["section_title"] == "4. Требования"
    assert out["items"][0]["fragment_index"] == 0


def test_numbered_heading_stub_skipped() -> None:
    structure = {
        "sections": [
            {"title": "Раздел", "content_text": "2.3 Общие положения"},
        ]
    }
    out = _ur(structure, "")
    assert out["item_count"] == 0


def test_short_fragment_skipped() -> None:
    out = _ur({"sections": []}, "Узел должен быть стабилен.")
    assert out["item_count"] == 0


def test_acceptance_phrase_makes_fragment_verifiable() -> None:
    sentence = "Качество модуля должно подтверждаться регрессионными тестами."
    out = _ur({"sections": []}, sentence)
    assert out["item_count"] == 0


def test_fallback_to_full_text_when_no_section_body() -> None:
    structure = {"sections": [{"title": "Пустой", "content_text": ""}]}
    full = "Компонент должен оставаться отзывчивым при пиковой нагрузке."
    out = _ur(structure, full)
    assert out["item_count"] == 1
    assert "section_title" not in out["items"][0]
