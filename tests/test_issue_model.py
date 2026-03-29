"""Tests for Stage 13.1 internal issue model and helpers."""

from __future__ import annotations

import pytest

from backend.app.reporting.issue_model import (
    Issue,
    IssueLocation,
    issue_from_vague_wording_finding,
    issue_to_dict,
    make_issue,
    make_issue_location,
    normalize_issue_severity,
)


def test_make_issue_strips_and_copies_metadata() -> None:
    issue = make_issue(
        check_key="  foo_check  ",
        issue_code="  code  ",
        message="  Сообщение  ",
        fragment_text="  фрагмент  ",
        section_title="  Раздел  ",
        metadata={"a": 1},
        severity="  warning  ",
    )
    assert issue.check_key == "foo_check"
    assert issue.issue_code == "code"
    assert issue.message == "Сообщение"
    assert issue.fragment_text == "фрагмент"
    assert issue.section_title == "Раздел"
    assert issue.metadata == {"a": 1}
    assert issue.severity == "warning"
    issue.metadata["b"] = 2
    assert "b" not in make_issue(
        check_key="x", issue_code="y", message="z", metadata={"a": 1}
    ).metadata


def test_make_issue_empty_required_raises() -> None:
    with pytest.raises(ValueError, match="check_key"):
        make_issue(check_key="", issue_code="c", message="m")
    with pytest.raises(ValueError, match="issue_code"):
        make_issue(check_key="k", issue_code="  ", message="m")
    with pytest.raises(ValueError, match="message"):
        make_issue(check_key="k", issue_code="c", message="")


def test_make_issue_severity_all_allowed_values() -> None:
    for sev in ("critical", "warning", "recommendation"):
        issue = make_issue(check_key="k", issue_code="c", message="m", severity=sev)
        assert issue.severity == sev


def test_make_issue_invalid_severity_raises() -> None:
    with pytest.raises(ValueError, match="severity"):
        make_issue(check_key="k", issue_code="c", message="m", severity="info")


def test_make_issue_blank_severity_becomes_none() -> None:
    issue = make_issue(check_key="k", issue_code="c", message="m", severity="   ")
    assert issue.severity is None


def test_issue_post_init_rejects_invalid_severity() -> None:
    with pytest.raises(ValueError, match="severity"):
        Issue(check_key="k", issue_code="c", message="m", severity="bad")  # type: ignore[arg-type]


def test_normalize_issue_severity() -> None:
    assert normalize_issue_severity(None) is None
    assert normalize_issue_severity("  warning  ") == "warning"
    with pytest.raises(ValueError, match="severity"):
        normalize_issue_severity("unknown")


def test_issue_to_dict_includes_severity_when_set() -> None:
    issue = make_issue(
        check_key="k",
        issue_code="c",
        message="m",
        severity="critical",
    )
    assert issue_to_dict(issue)["severity"] == "critical"


def test_issue_to_dict_includes_recommendation_when_set() -> None:
    issue = make_issue(
        check_key="k",
        issue_code="c",
        message="m",
        recommendation="  Подсказка  ",
    )
    d = issue_to_dict(issue)
    assert d["recommendation"] == "Подсказка"


def test_make_issue_blank_recommendation_omitted_in_dict() -> None:
    issue = make_issue(check_key="k", issue_code="c", message="m", recommendation="   ")
    assert issue.recommendation is None
    assert "recommendation" not in issue_to_dict(issue)


def test_make_issue_optional_none_omitted_in_dict() -> None:
    issue = make_issue(check_key="k", issue_code="c", message="текст")
    d = issue_to_dict(issue)
    assert d == {
        "check_key": "k",
        "issue_code": "c",
        "message": "текст",
        "metadata": {},
    }
    assert "fragment_text" not in d
    assert "section_title" not in d
    assert "severity" not in d
    assert "locations" not in d


def test_issue_to_dict_locations_compact() -> None:
    loc = make_issue_location(block_index=1, line_index=2)
    issue = make_issue(
        check_key="figure_references_check",
        issue_code="figure.missing_declaration",
        message="Упоминание рисунка без подписи.",
        locations=(loc,),
    )
    d = issue_to_dict(issue)
    assert d["locations"] == [{"block_index": 1, "line_index": 2}]


def test_issue_to_dict_skips_empty_location_entries() -> None:
    empty = IssueLocation()
    full = make_issue_location(block_index=0)
    issue = make_issue(
        check_key="k",
        issue_code="c",
        message="m",
        locations=(empty, full),
    )
    d = issue_to_dict(issue)
    assert d["locations"] == [{"block_index": 0}]


def test_issue_from_vague_wording_finding() -> None:
    finding = {
        "phrase": "быстро",
        "match_type": "dictionary_phrase",
        "text_excerpt": "... быстро ...",
        "source_kind": "full_text",
        "category": "speed",
        "description": "Не содержит измеримого критерия времени",
    }
    issue = issue_from_vague_wording_finding(finding)
    assert issue.check_key == "vague_wording_check"
    assert issue.issue_code == "vague_wording.dictionary_phrase"
    assert issue.message == "Не содержит измеримого критерия времени"
    assert issue.fragment_text == "... быстро ..."
    assert issue.metadata["phrase"] == "быстро"
    d = issue_to_dict(issue)
    assert d["fragment_text"] == "... быстро ..."
    assert issue.severity == "recommendation"
    assert d["severity"] == "recommendation"


def test_issue_from_vague_wording_finding_fallback_message() -> None:
    issue = issue_from_vague_wording_finding({"phrase": "скоро", "match_type": "dictionary_phrase"})
    assert "«скоро»" in issue.message
