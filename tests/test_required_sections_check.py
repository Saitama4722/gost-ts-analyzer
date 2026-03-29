"""Tests for Stage 8.1 required-section presence check."""

from backend.app.checks.required_sections_check import check_required_sections_presence
from backend.app.rules.section_rules import REQUIRED_SECTIONS
from backend.app.structure_builder import add_section_tree
from backend.app.structure_detector import detect_structure
from backend.app.structure_enricher import enrich_structure


def _enriched_from_blocks(blocks: list[str]) -> dict:
    raw = add_section_tree(detect_structure(blocks))
    return enrich_structure(raw, blocks)


def test_empty_sections_all_missing() -> None:
    out = check_required_sections_presence({"sections": []})
    rsc = out["required_sections_check"]
    assert rsc["present"] == []
    assert rsc["missing"] == list(REQUIRED_SECTIONS)


def test_invalid_sections_treated_as_empty() -> None:
    out = check_required_sections_presence({"sections": "not-a-list"})  # type: ignore[arg-type]
    assert out["required_sections_check"]["missing"] == list(REQUIRED_SECTIONS)


def test_alias_matches_introduction() -> None:
    # Plain "Общие сведения" is not a detected heading in 6.1; use manual structure
    # to assert rule-driven alias matching only.
    structure = {
        "sections": [
            {
                "title": "Общие сведения",
                "start_block": 0,
                "end_block": 0,
                "content_blocks": [],
                "content_text": "",
            },
        ]
    }
    rsc = check_required_sections_presence(structure)["required_sections_check"]
    assert "introduction" in rsc["present"]
    assert "introduction" not in rsc["missing"]


def test_numbered_alias_detected_in_pipeline() -> None:
    blocks = ["1. Общие сведения", "Body."]
    enriched = _enriched_from_blocks(blocks)
    rsc = check_required_sections_presence(enriched)["required_sections_check"]
    assert "introduction" in rsc["present"]


def test_numbered_title_strips_index_for_match() -> None:
    blocks = ["1. Критерии приёмки", "Text."]
    enriched = _enriched_from_blocks(blocks)
    rsc = check_required_sections_presence(enriched)["required_sections_check"]
    assert "acceptance_criteria" in rsc["present"]


def test_duplicate_headings_single_present_key() -> None:
    blocks = [
        "Введение",
        "A.",
        "Введение",
        "B.",
    ]
    enriched = _enriched_from_blocks(blocks)
    rsc = check_required_sections_presence(enriched)["required_sections_check"]
    assert rsc["present"].count("introduction") == 1


def test_multiple_required_found() -> None:
    blocks = [
        "Введение",
        "1. Назначение",
        "2. Область применения",
        "3. Функциональные требования",
    ]
    enriched = _enriched_from_blocks(blocks)
    rsc = check_required_sections_presence(enriched)["required_sections_check"]
    for key in (
        "introduction",
        "purpose",
        "scope",
        "functional_requirements",
    ):
        assert key in rsc["present"]
        assert key not in rsc["missing"]


def test_uppercase_heading_matches() -> None:
    blocks = ["НАЗНАЧЕНИЕ РАЗРАБОТКИ"]
    enriched = _enriched_from_blocks(blocks)
    rsc = check_required_sections_presence(enriched)["required_sections_check"]
    assert "purpose" in rsc["present"]
