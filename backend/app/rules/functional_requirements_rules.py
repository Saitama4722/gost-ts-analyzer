"""Stage 9.3: signals for functional-requirements presence (headings and text phrases).

Matching logic lives in ``backend.app.checks.functional_requirements_check``; this
module holds only explicit rule data. Phrases are chosen to point to functions or
required system capabilities, not generic «требования» alone.
"""

from __future__ import annotations

# Section titles (equality after shared heading normalization).
FUNCTIONAL_REQUIREMENTS_SECTION_HEADINGS: tuple[str, ...] = (
    "Функциональные требования",
    "Требования к функциональности",
    "Требования к функциям",
    "Функции системы",
    "Функции программного средства",
)

# Phrases in collapsed, case-folded full document text (order = priority).
FUNCTIONAL_REQUIREMENTS_TEXT_PHRASES: tuple[str, ...] = (
    "функциональные требования включают",
    "к функциям системы относятся",
    "должны быть реализованы функции",
    "программа должна обеспечивать",
    "система должна обеспечивать",
    "система должна выполнять",
)
