"""Tests for Stage 8.2 required-section order check."""

from backend.app.checks.section_order_check import check_section_order
from backend.app.structure_builder import add_section_tree
from backend.app.structure_detector import detect_structure
from backend.app.structure_enricher import enrich_structure


def _enriched_from_blocks(blocks: list[str]) -> dict:
    raw = add_section_tree(detect_structure(blocks))
    return enrich_structure(raw, blocks)


def test_empty_structure_order_ok() -> None:
    out = check_section_order({"sections": []})
    soc = out["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == []
    assert soc["expected_order_subset"] == []
    assert soc["violations"] == []


def test_invalid_sections_treated_as_empty() -> None:
    out = check_section_order({"sections": "x"})  # type: ignore[arg-type]
    soc = out["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == []


def test_single_detected_section_ok() -> None:
    blocks = ["Введение", "Text."]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == ["introduction"]
    assert soc["expected_order_subset"] == ["introduction"]


def test_correct_multi_section_order() -> None:
    blocks = [
        "Введение",
        "A.",
        "1. Назначение",
        "B.",
        "2. Область применения",
    ]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == ["introduction", "purpose", "scope"]
    assert soc["expected_order_subset"] == ["introduction", "purpose", "scope"]


def test_non_required_headings_between_ignored() -> None:
    blocks = [
        "Введение",
        "Произвольный раздел",
        "1. Назначение",
    ]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == ["introduction", "purpose"]


def test_duplicate_required_heading_single_order_slot() -> None:
    blocks = [
        "Введение",
        "A.",
        "Введение",
        "1. Назначение",
    ]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["detected_order"] == ["introduction", "purpose"]
    assert soc["is_correct"] is True


def test_swapped_sections_not_correct() -> None:
    blocks = [
        "1. Назначение",
        "A.",
        "Введение",
    ]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["is_correct"] is False
    assert soc["detected_order"] == ["purpose", "introduction"]
    assert soc["expected_order_subset"] == ["introduction", "purpose"]
    assert len(soc["violations"]) == 1
    v = soc["violations"][0]
    assert v["index"] == 0
    assert v["expected_key"] == "introduction"
    assert v["found_key"] == "purpose"


def test_missing_sections_do_not_fail_order() -> None:
    blocks = [
        "Введение",
        "1. Область применения",
    ]
    enriched = _enriched_from_blocks(blocks)
    soc = check_section_order(enriched)["section_order_check"]
    assert soc["is_correct"] is True
    assert soc["detected_order"] == ["introduction", "scope"]
    assert soc["expected_order_subset"] == ["introduction", "scope"]
