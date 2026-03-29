"""Tests for Stage 13.3 document-level issues aggregation."""

from __future__ import annotations

from backend.app.reporting.issue_model import make_issue
from backend.app.reporting.issues_builder import (
    build_document_issues,
    build_document_issues_serialized,
    with_recommendation,
)


def test_build_document_issues_empty_and_none() -> None:
    assert build_document_issues({}) == []
    assert build_document_issues(None) == []
    assert build_document_issues_serialized({}) == []


def test_build_document_issues_ignores_unsupported_checks() -> None:
    issues = build_document_issues({"unknown_check": {"x": 1}})
    assert issues == []


def test_build_document_issues_deterministic_order() -> None:
    checks = {
        "terminology_consistency_check": {
            "has_findings": True,
            "item_count": 1,
            "items": [
                {
                    "term_key": "z_term",
                    "canonical": "Z",
                    "used_variants": ["a", "b"],
                    "preferred_variant": "Z",
                    "reason": "термин z",
                    "example_snippet": "z",
                }
            ],
        },
        "vague_wording_check": {
            "has_findings": True,
            "finding_count": 1,
            "findings": [
                {
                    "phrase": "быстро",
                    "match_type": "dictionary_phrase",
                    "text_excerpt": "… быстро …",
                    "source_kind": "full_text",
                    "category": "speed",
                    "description": "Нет измеримого критерия",
                }
            ],
        },
    }
    keys = [i.check_key for i in build_document_issues(checks)]
    assert keys == sorted(keys)


def test_adapter_subset_coverage() -> None:
    checks = {
        "vague_wording_check": {
            "findings": [
                {
                    "phrase": "удобно",
                    "match_type": "dictionary_phrase",
                    "text_excerpt": "удобный интерфейс",
                    "source_kind": "full_text",
                    "category": "ux",
                    "description": "Субъективная оценка без критериев",
                }
            ],
            "has_findings": True,
            "finding_count": 1,
        },
        "unverifiable_requirements_check": {
            "items": [
                {
                    "text": "Система должна работать стабильно.",
                    "reason": "формулировка требования без измеримых критериев",
                    "obligation_marker": "должна",
                    "fragment_index": 3,
                    "section_title": "Требования",
                }
            ],
            "has_findings": True,
            "item_count": 1,
        },
        "figure_references_check": {
            "missing_declarations": [2],
            "unreferenced_figures": [],
            "duplicate_declarations": [],
            "caption_numbering_gaps": [],
            "mentions": [
                {
                    "number": 2,
                    "block_index": 0,
                    "line_index": 1,
                    "mention_text": "рис. 2",
                    "line": "см. рис. 2",
                }
            ],
            "declarations": [],
        },
        "terminology_consistency_check": {
            "items": [
                {
                    "term_key": "interface",
                    "canonical": "интерфейс",
                    "used_variants": ["интерфейс", "UI"],
                    "preferred_variant": "интерфейс",
                    "reason": "для одного термина использованы разные варианты наименования",
                    "example_snippet": "... UI ...",
                }
            ],
            "has_findings": True,
            "item_count": 1,
        },
        "duplicate_formulations_check": {
            "items": [
                {
                    "kind": "exact_duplicate",
                    "text": "Один и тот же текст.",
                    "occurrences": 2,
                    "reason": "в документе повторяется одинаковая формулировка",
                    "fragment_indexes": [0, 5],
                    "section_titles": ["А", "Б"],
                },
                {
                    "kind": "near_duplicate",
                    "text_a": "Формулировка почти одна",
                    "text_b": "Формулировка почти одна же",
                    "similarity": 0.9,
                    "reason": "обнаружены очень похожие формулировки",
                },
            ],
            "has_findings": True,
            "item_count": 2,
        },
    }
    serialized = build_document_issues_serialized(checks)
    by_check: dict[str, int] = {}
    for row in serialized:
        by_check[row["check_key"]] = by_check.get(row["check_key"], 0) + 1
    assert by_check["vague_wording_check"] == 1
    assert by_check["unverifiable_requirements_check"] == 1
    assert by_check["figure_references_check"] == 1
    assert by_check["terminology_consistency_check"] == 1
    assert by_check["duplicate_formulations_check"] == 2

    uni = next(r for r in serialized if r["check_key"] == "unverifiable_requirements_check")
    assert uni["section_title"] == "Требования"
    assert uni["severity"] == "warning"
    assert "locations" in uni

    fig = next(r for r in serialized if r["issue_code"] == "figure.missing_declaration")
    assert fig["locations"] == [{"block_index": 0, "line_index": 1}]

    vague = next(r for r in serialized if r["check_key"] == "vague_wording_check")
    assert vague["severity"] == "recommendation"
    assert vague["recommendation"] == (
        "Уточните формулировку и замените расплывчатое слово на измеримый критерий."
    )
    assert "recommendation" in uni
    assert "recommendation" in fig
    term = next(r for r in serialized if r["check_key"] == "terminology_consistency_check")
    assert term["recommendation"] == "Используйте один вариант термина во всём документе."
    dups = [r for r in serialized if r["check_key"] == "duplicate_formulations_check"]
    assert all("recommendation" in r for r in dups)


def test_with_recommendation_preserves_explicit_value() -> None:
    base = make_issue(
        check_key="k",
        issue_code="figure.missing_declaration",
        message="m",
        recommendation="Своя подсказка",
    )
    assert with_recommendation(base).recommendation == "Своя подсказка"


def test_malformed_lists_skipped_safely() -> None:
    checks = {
        "vague_wording_check": {"findings": "not-a-list"},
        "unverifiable_requirements_check": {"items": None},
        "figure_references_check": {"missing_declarations": ["x"]},
    }
    assert build_document_issues(checks) == []
