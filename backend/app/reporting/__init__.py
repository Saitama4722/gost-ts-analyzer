"""Internal reporting primitives (issue model, future aggregation)."""

from backend.app.reporting.issue_model import (
    ALLOWED_ISSUE_SEVERITIES,
    Issue,
    IssueLocation,
    IssueSeverity,
    issue_from_vague_wording_finding,
    issue_to_dict,
    make_issue,
    make_issue_location,
    normalize_issue_severity,
)

__all__ = [
    "ALLOWED_ISSUE_SEVERITIES",
    "Issue",
    "IssueLocation",
    "IssueSeverity",
    "issue_from_vague_wording_finding",
    "issue_to_dict",
    "make_issue",
    "make_issue_location",
    "normalize_issue_severity",
]
