"""Tests for Stage 13.5 final analysis report from normalized issues."""

from __future__ import annotations

from backend.app.reporting.report_builder import (
    build_analysis_report,
    conclusion_and_status,
)


def test_report_empty_and_none() -> None:
    r0 = build_analysis_report([])
    assert r0["summary"]["total_issues"] == 0
    assert r0["summary"]["status"] == "no_issues"
    assert r0["summary"]["conclusion"] == "Существенных замечаний не обнаружено."
    assert r0["summary"]["by_severity"] == {
        "critical": 0,
        "warning": 0,
        "recommendation": 0,
    }
    assert r0["summary"]["issues_without_severity"] == 0
    assert r0["summary"]["by_check"] == {}
    assert r0["summary"]["issues_with_recommendations"] == 0
    assert r0["issues"] == []
    assert r0["groups"]["by_severity"]["unspecified"] == []
    assert r0["groups"]["by_check"] == {}

    r1 = build_analysis_report(None)
    assert r1["issues"] == []
    assert r1["summary"]["total_issues"] == 0


def test_report_only_recommendations_conclusion() -> None:
    issues = [
        {
            "check_key": "vague_wording_check",
            "issue_code": "vague_wording.x",
            "message": "m",
            "metadata": {},
            "severity": "recommendation",
            "recommendation": "hint",
        }
    ]
    rep = build_analysis_report(issues)
    assert rep["summary"]["status"] == "recommendations_only"
    assert rep["summary"]["conclusion"] == (
        "Документ в целом корректен, но есть рекомендации по улучшению."
    )
    assert rep["summary"]["by_severity"]["recommendation"] == 1
    assert rep["summary"]["issues_with_recommendations"] == 1
    assert rep["issues"] is issues
    assert rep["groups"]["by_severity"]["recommendation"] == issues


def test_report_warning_triggers_needs_review() -> None:
    issues = [
        {
            "check_key": "unverifiable_requirements_check",
            "issue_code": "unverifiable.obligation_without_metrics",
            "message": "m",
            "metadata": {},
            "severity": "warning",
        }
    ]
    rep = build_analysis_report(issues)
    assert rep["summary"]["status"] == "needs_review"
    assert rep["summary"]["conclusion"] == (
        "В документе обнаружены замечания, требующие доработки."
    )


def test_report_invalid_severity_goes_unspecified() -> None:
    issues = [
        {
            "check_key": "x",
            "issue_code": "c",
            "message": "m",
            "metadata": {},
            "severity": "not_a_real_severity",
        }
    ]
    rep = build_analysis_report(issues)
    assert rep["summary"]["issues_without_severity"] == 1
    assert rep["summary"]["by_severity"] == {
        "critical": 0,
        "warning": 0,
        "recommendation": 0,
    }
    assert rep["groups"]["by_severity"]["unspecified"] == issues


def test_report_missing_check_key_unknown() -> None:
    issues = [
        {
            "issue_code": "c",
            "message": "m",
            "metadata": {},
            "severity": "recommendation",
        }
    ]
    rep = build_analysis_report(issues)
    assert rep["summary"]["by_check"] == {"unknown": 1}
    assert list(rep["groups"]["by_check"].keys()) == ["unknown"]


def test_report_skips_non_dict_entries() -> None:
    raw: list = [
        "skip",
        {
            "check_key": "k",
            "issue_code": "c",
            "message": "m",
            "metadata": {},
            "severity": "recommendation",
        },
    ]
    rep = build_analysis_report(raw)
    assert rep["summary"]["total_issues"] == 1
    assert rep["issues"] is raw


def test_report_by_check_keys_sorted() -> None:
    issues = [
        {
            "check_key": "zebra",
            "issue_code": "a",
            "message": "m",
            "metadata": {},
            "severity": "recommendation",
        },
        {
            "check_key": "alpha",
            "issue_code": "b",
            "message": "m",
            "metadata": {},
            "severity": "recommendation",
        },
    ]
    rep = build_analysis_report(issues)
    assert list(rep["summary"]["by_check"].keys()) == ["alpha", "zebra"]
    assert list(rep["groups"]["by_check"].keys()) == ["alpha", "zebra"]


def test_conclusion_and_status_unit() -> None:
    assert conclusion_and_status(
        total_issues=0, by_severity={"critical": 0, "warning": 0, "recommendation": 0}
    ) == ("Существенных замечаний не обнаружено.", "no_issues")
    assert conclusion_and_status(
        total_issues=1, by_severity={"critical": 0, "warning": 0, "recommendation": 1}
    )[1] == "recommendations_only"
    assert conclusion_and_status(
        total_issues=2, by_severity={"critical": 0, "warning": 1, "recommendation": 1}
    )[1] == "needs_review"
