"""Document-level final analysis report from normalized serialized issues (Stage 13.5).

Builds a compact JSON-friendly ``report`` object: counts, grouping, and a short
rule-based Russian conclusion. Input is the same list as ``response["issues"]``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.app.reporting.issue_model import normalize_issue_severity

# Stable severity bucket order for counts and group lists.
_SEVERITY_ORDER: tuple[str, ...] = ("critical", "warning", "recommendation")

_MSG_NO_ISSUES = "Существенных замечаний не обнаружено."
_MSG_RECOMMENDATIONS_ONLY = (
    "Документ в целом корректен, но есть рекомендации по улучшению."
)
_MSG_NEEDS_WORK = "В документе обнаружены замечания, требующие доработки."


def _safe_severity(issue: Mapping[str, Any]) -> str | None:
    """Return a known severity or ``None`` if missing/invalid (no exceptions)."""
    try:
        return normalize_issue_severity(issue.get("severity"))
    except ValueError:
        return None


def _check_key_for_issue(issue: Mapping[str, Any]) -> str:
    raw = issue.get("check_key")
    if raw is None:
        return "unknown"
    s = str(raw).strip()
    return s if s else "unknown"


def _has_recommendation_text(issue: Mapping[str, Any]) -> bool:
    r = issue.get("recommendation")
    if r is None:
        return False
    return bool(str(r).strip())


def conclusion_and_status(
    *,
    total_issues: int,
    by_severity: Mapping[str, int],
) -> tuple[str, str]:
    """Return ``(conclusion_ru, status)`` with deterministic rule-based text.

    ``status`` is a short machine token: ``no_issues``, ``recommendations_only``,
    ``needs_review``.
    """
    if total_issues == 0:
        return _MSG_NO_ISSUES, "no_issues"
    crit = int(by_severity.get("critical", 0))
    warn = int(by_severity.get("warning", 0))
    if crit > 0 or warn > 0:
        return _MSG_NEEDS_WORK, "needs_review"
    return _MSG_RECOMMENDATIONS_ONLY, "recommendations_only"


def build_analysis_report(
    serialized_issues: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Build the final report dict from the normalized issues list (JSON-shaped dicts).

    - Counts only ``critical`` / ``warning`` / ``recommendation``; other or missing
      severity counts toward ``issues_without_severity`` and list under
      ``groups["by_severity"]["unspecified"]``.
    - Non-dict entries in ``serialized_issues`` are skipped for all aggregates.
    - ``report["issues"]`` reuses the same list instance when input is a list.
    """
    raw_list = serialized_issues if isinstance(serialized_issues, list) else []
    issues_out: list[dict[str, Any]] = [
        x for x in raw_list if isinstance(x, dict)
    ]

    by_severity: dict[str, int] = {k: 0 for k in _SEVERITY_ORDER}
    issues_without_severity = 0
    by_check_counts: dict[str, int] = {}
    groups_by_severity: dict[str, list[dict[str, Any]]] = {
        "critical": [],
        "warning": [],
        "recommendation": [],
        "unspecified": [],
    }
    groups_by_check: dict[str, list[dict[str, Any]]] = {}
    recommendations_count = 0

    for issue in issues_out:
        sev = _safe_severity(issue)
        if sev is not None:
            by_severity[sev] = by_severity.get(sev, 0) + 1
            groups_by_severity[sev].append(issue)
        else:
            issues_without_severity += 1
            groups_by_severity["unspecified"].append(issue)

        ck = _check_key_for_issue(issue)
        by_check_counts[ck] = by_check_counts.get(ck, 0) + 1
        if ck not in groups_by_check:
            groups_by_check[ck] = []
        groups_by_check[ck].append(issue)

        if _has_recommendation_text(issue):
            recommendations_count += 1

    total_issues = len(issues_out)
    by_check_sorted = {k: by_check_counts[k] for k in sorted(by_check_counts.keys())}
    groups_by_check_sorted = {
        k: groups_by_check[k] for k in sorted(groups_by_check.keys())
    }

    conclusion, status = conclusion_and_status(
        total_issues=total_issues,
        by_severity=by_severity,
    )

    summary: dict[str, Any] = {
        "status": status,
        "total_issues": total_issues,
        "by_severity": dict(by_severity),
        "issues_without_severity": issues_without_severity,
        "by_check": by_check_sorted,
        "issues_with_recommendations": recommendations_count,
        "conclusion": conclusion,
    }

    return {
        "summary": summary,
        "issues": serialized_issues if isinstance(serialized_issues, list) else issues_out,
        "groups": {
            "by_severity": groups_by_severity,
            "by_check": groups_by_check_sorted,
        },
    }


__all__ = ["build_analysis_report", "conclusion_and_status"]
