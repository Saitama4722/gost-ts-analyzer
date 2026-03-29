"""Stage 9.2: signals for document scope / application-area presence.

Matching logic lives in ``backend.app.checks.scope_check``; this module holds
only explicit rule data. Kept separate from purpose (9.1) and structural scope key.
"""

from __future__ import annotations

# Section titles (equality after shared heading normalization).
SCOPE_SECTION_HEADINGS: tuple[str, ...] = (
    "Область применения",
    "Сфера применения",
    "Область использования",
    "Область действия",
)

# Phrases in collapsed, case-folded full document text (order = priority).
SCOPE_TEXT_PHRASES: tuple[str, ...] = (
    "Настоящий документ распространяется на",
    "Документ предназначен для применения",
    "Область применения документа",
    "Сфера применения",
    "Документ применяется",
)
