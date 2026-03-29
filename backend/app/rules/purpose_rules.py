"""Stage 9.1: signals for document purpose presence (headings and text phrases).

Matching logic lives in ``backend.app.checks.purpose_check``; this module holds
only explicit rule data.
"""

from __future__ import annotations

# Section titles treated as purpose-related (equality after shared heading normalization).
PURPOSE_SECTION_HEADINGS: tuple[str, ...] = (
    "Цель",
    "Цель документа",
    "Назначение",
    "Назначение документа",
)

# Phrases searched in collapsed, case-folded full document text (order = priority).
PURPOSE_TEXT_PHRASES: tuple[str, ...] = (
    "Цель документа",
    "Целью документа является",
    "Документ предназначен для",
    "Назначение документа",
)
