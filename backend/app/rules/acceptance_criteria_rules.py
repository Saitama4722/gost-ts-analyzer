"""Stage 9.5: signals for acceptance criteria / requirement verifiability presence.

Matching logic lives in ``backend.app.checks.acceptance_criteria_check``; this module
holds only explicit rule data. Signals target acceptance conditions, verification
methods, or explicit confirmability — not generic «проверка» / «тест» alone.
"""

from __future__ import annotations

# Section titles (equality after shared heading normalization).
ACCEPTANCE_CRITERIA_SECTION_HEADINGS: tuple[str, ...] = (
    "Критерии приёмки",
    "Критерии приемки",
    "Критерии приёмочных испытаний",
    "Приёмочные испытания",
    "Приемочные испытания",
    "Порядок приёмки",
    "Порядок приемки",
    "Методика проверки",
    "Проверка требований",
    "Контроль и приёмка",
    "Контроль и приемка",
    "Условия приёмки",
    "Условия приемки",
)

# Phrases in collapsed, case-folded full document text (order = priority: specific first).
ACCEPTANCE_CRITERIA_TEXT_PHRASES: tuple[str, ...] = (
    "требование считается выполненным, если",
    "критерием приёмки является",
    "критерием приемки является",
    "считается выполненным при",
    "проверяется путём",
    "проверяется путем",
    "должно подтверждаться",
    "результат испытаний должен",
    "приёмка осуществляется",
    "приемка осуществляется",
    "соответствие проверяется",
    "подлежит проверке",
)
