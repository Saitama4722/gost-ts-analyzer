"""Unified internal model for a single check finding / violation.

Raw check modules keep their native result shapes; this module is the common
denominator for future aggregation and export (Stage 13+).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, TypeAlias, cast

# Machine-readable severity values (extend by updating this set and alias together).
ALLOWED_ISSUE_SEVERITIES: frozenset[str] = frozenset(
    ("critical", "warning", "recommendation")
)
IssueSeverity: TypeAlias = Literal["critical", "warning", "recommendation"]


def normalize_issue_severity(value: object | None) -> IssueSeverity | None:
    """Return a valid severity, ``None`` if omitted/blank, or raise on invalid values."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s not in ALLOWED_ISSUE_SEVERITIES:
        raise ValueError(
            "severity must be one of "
            f"{sorted(ALLOWED_ISSUE_SEVERITIES)!r}, got {value!r}"
        )
    return cast(IssueSeverity, s)


@dataclass
class IssueLocation:
    """Optional pointer into the document (block / line / fragment index)."""

    block_index: int | None = None
    line_index: int | None = None
    fragment_index: int | None = None


@dataclass
class Issue:
    """One normalized issue produced by any compliance check."""

    check_key: str
    issue_code: str
    message: str
    fragment_text: str | None = None
    section_title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    severity: IssueSeverity | None = None
    locations: tuple[IssueLocation, ...] | None = None
    recommendation: str | None = None

    def __post_init__(self) -> None:
        if self.severity is not None and self.severity not in ALLOWED_ISSUE_SEVERITIES:
            raise ValueError(
                "severity must be one of "
                f"{sorted(ALLOWED_ISSUE_SEVERITIES)!r}, got {self.severity!r}"
            )


def make_issue_location(
    *,
    block_index: int | None = None,
    line_index: int | None = None,
    fragment_index: int | None = None,
) -> IssueLocation:
    """Build a location record (any subset of indexes is allowed)."""
    return IssueLocation(
        block_index=block_index,
        line_index=line_index,
        fragment_index=fragment_index,
    )


def make_issue(
    *,
    check_key: str,
    issue_code: str,
    message: str,
    fragment_text: str | None = None,
    section_title: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    severity: object | None = None,
    locations: tuple[IssueLocation, ...] | None = None,
    recommendation: object | None = None,
) -> Issue:
    """Construct an ``Issue`` with stripped required strings and a copied ``metadata`` dict.

    ``severity`` defaults to ``None`` when omitted or blank. Non-blank values must be
    one of: critical, warning, recommendation.
    """
    ck = str(check_key).strip()
    ic = str(issue_code).strip()
    msg = str(message).strip()
    if not ck:
        raise ValueError("check_key must be non-empty")
    if not ic:
        raise ValueError("issue_code must be non-empty")
    if not msg:
        raise ValueError("message must be non-empty")
    meta = dict(metadata) if metadata else {}
    st = str(section_title).strip() if section_title is not None else None
    st_out = st if st else None
    ft = str(fragment_text).strip() if fragment_text is not None else None
    ft_out = ft if ft else None
    sev_out = normalize_issue_severity(severity)
    rec_out: str | None = None
    if recommendation is not None:
        r = str(recommendation).strip()
        rec_out = r if r else None
    return Issue(
        check_key=ck,
        issue_code=ic,
        message=msg,
        fragment_text=ft_out,
        section_title=st_out,
        metadata=meta,
        severity=sev_out,
        locations=locations,
        recommendation=rec_out,
    )


def _location_to_dict(loc: IssueLocation) -> dict[str, int]:
    d: dict[str, int] = {}
    if loc.block_index is not None:
        d["block_index"] = loc.block_index
    if loc.line_index is not None:
        d["line_index"] = loc.line_index
    if loc.fragment_index is not None:
        d["fragment_index"] = loc.fragment_index
    return d


def issue_to_dict(issue: Issue) -> dict[str, Any]:
    """Serialize an issue to plain JSON-friendly dicts (locations omit unset indexes)."""
    out: dict[str, Any] = {
        "check_key": issue.check_key,
        "issue_code": issue.issue_code,
        "message": issue.message,
        "metadata": dict(issue.metadata),
    }
    if issue.fragment_text is not None:
        out["fragment_text"] = issue.fragment_text
    if issue.section_title is not None:
        out["section_title"] = issue.section_title
    if issue.severity is not None:
        out["severity"] = issue.severity
    if issue.recommendation is not None:
        out["recommendation"] = issue.recommendation
    if issue.locations:
        locs = [d for loc in issue.locations if (d := _location_to_dict(loc))]
        if locs:
            out["locations"] = locs
    return out


def issue_from_vague_wording_finding(finding: Mapping[str, Any]) -> Issue:
    """Minimal adapter: one Stage 10.1 ``findings[]`` item -> ``Issue``.

    Keeps raw finding fields in ``metadata`` for traceability; ``message`` uses the
    dictionary's Russian ``description`` when present.
    """
    phrase = str(finding.get("phrase") or "").strip()
    desc = str(finding.get("description") or "").strip()
    message = desc if desc else f"Обнаружена неконкретная формулировка: «{phrase}»."
    excerpt = finding.get("text_excerpt")
    if excerpt is not None:
        ex = str(excerpt).strip()
        fragment = ex if ex else None
    else:
        fragment = phrase or None
    match_type = str(finding.get("match_type") or "unknown").strip() or "unknown"
    meta = {k: finding[k] for k in ("phrase", "category", "match_type", "source_kind", "description") if k in finding}
    code = f"vague_wording.{match_type}"
    return make_issue(
        check_key="vague_wording_check",
        issue_code=code,
        message=message,
        fragment_text=fragment,
        metadata=meta,
        severity="recommendation",
    )
