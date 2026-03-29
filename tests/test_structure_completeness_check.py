"""Tests for Stage 8.3 structural completeness check."""

from backend.app.checks.required_sections_check import check_required_sections_presence
from backend.app.checks.structure_completeness_check import check_structure_completeness
from backend.app.rules.section_rules import REQUIRED_SECTIONS, REQUIRED_SECTION_TEMPLATES
from backend.app.structure_builder import add_section_tree
from backend.app.structure_detector import detect_structure
from backend.app.structure_enricher import enrich_structure


def _enriched_from_blocks(blocks: list[str]) -> dict:
    raw = add_section_tree(detect_structure(blocks))
    return enrich_structure(raw, blocks)


def test_empty_structure_incomplete_and_flags() -> None:
    structure: dict = {"sections": []}
    presence = check_required_sections_presence(structure)
    out = check_structure_completeness(structure, presence_result=presence)
    scc = out["structure_completeness_check"]
    assert scc["is_complete"] is False
    assert scc["required_total"] == len(REQUIRED_SECTIONS)
    assert scc["present_count"] == 0
    assert scc["missing_count"] == len(REQUIRED_SECTIONS)
    assert scc["completeness_ratio"] == 0.0
    assert scc["present"] == []
    assert scc["missing"] == list(REQUIRED_SECTIONS)
    assert scc["no_sections_detected"] is True
    assert scc["structure_sparse"] is True


def test_zero_required_total_does_not_crash() -> None:
    structure = {"sections": [{"title": "X", "start_block": 0, "end_block": 0}]}
    presence = {"required_sections_check": {"present": [], "missing": []}}
    out = check_structure_completeness(structure, presence_result=presence)
    scc = out["structure_completeness_check"]
    assert scc["required_total"] == 0
    assert scc["is_complete"] is True
    assert scc["completeness_ratio"] == 1.0
    assert scc["no_sections_detected"] is False


def test_without_presence_result_delegates_to_stage_81() -> None:
    structure = {"sections": []}
    out = check_structure_completeness(structure)
    scc = out["structure_completeness_check"]
    assert scc["missing_count"] == len(REQUIRED_SECTIONS)


def test_partial_completeness_counts_and_ratio() -> None:
    blocks = [
        "Введение",
        "1. Назначение",
        "2. Область применения",
    ]
    enriched = _enriched_from_blocks(blocks)
    presence = check_required_sections_presence(enriched)
    out = check_structure_completeness(enriched, presence_result=presence)
    scc = out["structure_completeness_check"]
    assert scc["present_count"] == 3
    assert scc["missing_count"] == len(REQUIRED_SECTIONS) - 3
    assert scc["is_complete"] is False
    expected_ratio = round(3 / len(REQUIRED_SECTIONS), 4)
    assert scc["completeness_ratio"] == expected_ratio
    assert scc["no_sections_detected"] is False
    assert scc["structure_sparse"] is False


def test_all_required_present_is_complete() -> None:
    sections = []
    for i, tpl in enumerate(REQUIRED_SECTION_TEMPLATES):
        sections.append(
            {
                "title": tpl["title"],
                "start_block": i,
                "end_block": i,
                "content_blocks": [],
                "content_text": "",
            }
        )
    structure = {"sections": sections}
    presence = check_required_sections_presence(structure)
    out = check_structure_completeness(structure, presence_result=presence)
    scc = out["structure_completeness_check"]
    assert scc["is_complete"] is True
    assert scc["missing_count"] == 0
    assert scc["completeness_ratio"] == 1.0
    assert scc["present"] == list(REQUIRED_SECTIONS)


def test_duplicate_headings_do_not_inflate_present_count() -> None:
    blocks = ["Введение", "A.", "Введение", "B."]
    enriched = _enriched_from_blocks(blocks)
    presence = check_required_sections_presence(enriched)
    out = check_structure_completeness(enriched, presence_result=presence)
    scc = out["structure_completeness_check"]
    assert scc["present_count"] == 1
    assert scc["present"].count("introduction") == 1
