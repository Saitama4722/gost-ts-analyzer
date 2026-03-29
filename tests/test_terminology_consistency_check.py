"""Tests for Stage 12.1 terminology consistency (glossary-driven)."""

from __future__ import annotations

from backend.app.checks.terminology_consistency_check import check_document_terminology_consistency


def _run(text: str) -> dict:
    return check_document_terminology_consistency({}, text)


def test_empty_text_no_findings() -> None:
    out = _run("")
    chk = out["terminology_consistency_check"]
    assert chk["has_findings"] is False
    assert chk["item_count"] == 0
    assert chk["items"] == []


def test_single_canonical_variant_only_no_finding() -> None:
    text = "В документе описано техническое задание и ещё раз техническое задание."
    chk = _run(text)["terminology_consistency_check"]
    assert chk["has_findings"] is False


def test_single_non_canonical_alias_only_no_finding() -> None:
    """Conservative: one glossary variant used consistently is not reported."""
    text = "Согласно ТЗ система должна работать. Далее по ТЗ уточняем детали."
    chk = _run(text)["terminology_consistency_check"]
    keys = {it["term_key"] for it in chk["items"]}
    assert "technical_specification" not in keys


def test_two_aliases_same_term_reported() -> None:
    text = "Оформить техническое задание по ГОСТ. Сокращённо далее используем ТЗ как основу."
    chk = _run(text)["terminology_consistency_check"]
    assert chk["has_findings"] is True
    ts_items = [it for it in chk["items"] if it["term_key"] == "technical_specification"]
    assert len(ts_items) == 1
    item = ts_items[0]
    assert set(item["used_variants"]) == {"тз", "техническое задание"}
    assert item["preferred_variant"] == "техническое задание"
    assert item["reason"]
    assert item["occurrence_count_by_variant"]["тз"] >= 1
    assert item["occurrence_count_by_variant"]["техническое задание"] >= 1
    assert "example_snippet" in item


def test_functional_singular_and_plural_variants_reported() -> None:
    text = "Функциональное требование X. Отдельно перечислены функциональные требования Y."
    chk = _run(text)["terminology_consistency_check"]
    fr = [it for it in chk["items"] if it["term_key"] == "functional_requirement"]
    assert len(fr) == 1
    assert set(fr[0]["used_variants"]) == {
        "функциональное требование",
        "функциональные требования",
    }


def test_longer_alias_does_not_double_count_shorter_embedded() -> None:
    """Only one variant when text uses the longer alias containing the shorter token."""
    text = "Модуль реализует пользовательский интерфейс для оператора."
    chk = _run(text)["terminology_consistency_check"]
    iface = [it for it in chk["items"] if it["term_key"] == "interface"]
    assert iface == []


def test_interface_two_distinct_aliases_reported() -> None:
    text = "Описан интерфейс системы. Отдельно описан пользовательский интерфейс целиком."
    chk = _run(text)["terminology_consistency_check"]
    iface = [it for it in chk["items"] if it["term_key"] == "interface"]
    assert len(iface) == 1
    assert set(iface[0]["used_variants"]) == {"интерфейс", "пользовательский интерфейс"}


def test_no_false_positive_substring_inside_unrelated_word() -> None:
    text = "Слово разделение не должно считаться вхождением термина раздел."
    chk = _run(text)["terminology_consistency_check"]
    sec = [it for it in chk["items"] if it["term_key"] == "section"]
    assert sec == []


def test_case_and_extra_spaces_normalized() -> None:
    text = "ТЕХНИЧЕСКОЕ  ЗАДАНИЕ оформлено. Потом снова тз."
    chk = _run(text)["terminology_consistency_check"]
    ts = [it for it in chk["items"] if it["term_key"] == "technical_specification"]
    assert len(ts) == 1
