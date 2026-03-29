"""Stage 9.4: signals for non-functional-requirements presence (headings and text phrases).

Matching logic lives in ``backend.app.checks.nonfunctional_requirements_check``; this
module holds only explicit rule data. Signals target quality attributes and
operational constraints, not generic «требования» or functional capability wording.
"""

from __future__ import annotations

# Section titles (equality after shared heading normalization).
NONFUNCTIONAL_REQUIREMENTS_SECTION_HEADINGS: tuple[str, ...] = (
    "Нефункциональные требования",
    "Требования к надёжности",
    "Требования к производительности",
    "Требования к безопасности",
    "Требования к удобству использования",
    "Требования к совместимости",
    "Требования к отказоустойчивости",
    "Требования к доступности",
    "Требования к сопровождаемости",
)

# Phrases in collapsed, case-folded full document text (order = priority).
NONFUNCTIONAL_REQUIREMENTS_TEXT_PHRASES: tuple[str, ...] = (
    "требования к надёжности",
    "требования к производительности",
    "требования к безопасности",
    "требования к удобству использования",
    "требования к совместимости",
    "время отклика не должно превышать",
    "система должна быть защищена",
    "доступность системы должна составлять",
    "должна обеспечиваться совместимость",
    "должно быть обеспечено восстановление",
    "должна обеспечиваться отказоустойчивость",
)
