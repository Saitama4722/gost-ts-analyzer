"""Section-related rule data: heading keywords and required-section templates.

``SECTION_KEYWORDS_FOR_HEADING_DETECTION`` is used by structure detection (6.1).
``REQUIRED_SECTION_TEMPLATES`` defines the expected ТЗ/ТТ sections (Stage 7.2).
Required-section **presence** is evaluated in ``backend.app.checks.required_sections_check``
(Stage 8.1). **Order** of detected required sections uses the same template order in
``backend.app.checks.section_order_check`` (Stage 8.2). **Completeness** summary
(Stage 8.3) is in ``backend.app.checks.structure_completeness_check``.
"""

from __future__ import annotations

from typing import Final, TypedDict


class RequiredSectionTemplate(TypedDict):
    """One required block in a technical specification / technical task document.

    * ``key`` — stable identifier for code and ordering.
    * ``title`` — canonical Russian heading text.
    * ``aliases`` — common variants for later fuzzy or normalized matching
      (should include ``title`` so checks can treat canonical and alias uniformly).
    """

    key: str
    title: str
    aliases: tuple[str, ...]


# Ordered template: suggested document order for future section-order checks.
REQUIRED_SECTION_TEMPLATES: Final[list[RequiredSectionTemplate]] = [
    {
        "key": "introduction",
        "title": "Введение",
        "aliases": (
            "Введение",
            "Общие сведения",
            "Общие положения",
        ),
    },
    {
        "key": "purpose",
        "title": "Назначение",
        "aliases": (
            "Назначение",
            "Назначение разработки",
            "Цель разработки",
            "Цель создания системы",
        ),
    },
    {
        "key": "scope",
        "title": "Область применения",
        "aliases": (
            "Область применения",
            "Область использования",
        ),
    },
    {
        "key": "functional_requirements",
        "title": "Функциональные требования",
        "aliases": (
            "Функциональные требования",
            "Требования к функциям",
            "Функции системы",
        ),
    },
    {
        "key": "nonfunctional_requirements",
        "title": "Нефункциональные требования",
        "aliases": (
            "Нефункциональные требования",
            "Общие нефункциональные требования",
        ),
    },
    {
        "key": "reliability_requirements",
        "title": "Требования к надёжности",
        "aliases": (
            "Требования к надёжности",
            "Надёжность",
            "Показатели надёжности",
        ),
    },
    {
        "key": "safety_requirements",
        "title": "Требования к безопасности",
        "aliases": (
            "Требования к безопасности",
            "Безопасность",
            "Информационная безопасность",
        ),
    },
    {
        "key": "performance_requirements",
        "title": "Требования к производительности",
        "aliases": (
            "Требования к производительности",
            "Производительность",
            "Требования к быстродействию",
        ),
    },
    {
        "key": "acceptance_criteria",
        "title": "Критерии приёмки",
        "aliases": (
            "Критерии приёмки",
            "Критерии приемки",
            "Порядок приёмки",
            "Порядок приемки",
            "Приёмка",
            "Приемка",
            "Условия приёмки",
            "Условия приемки",
        ),
    },
    {
        "key": "appendices",
        "title": "Приложения",
        "aliases": (
            "Приложения",
            "Приложение",
        ),
    },
    {
        "key": "used_sources",
        "title": "Перечень использованных источников",
        "aliases": (
            "Перечень использованных источников",
            "Список использованных источников",
            "Список литературы",
            "Библиографический список",
        ),
    },
]

# Stable keys in template order (for quick lookups and future order checks).
REQUIRED_SECTIONS: tuple[str, ...] = tuple(item["key"] for item in REQUIRED_SECTION_TEMPLATES)

# Same order as ``REQUIRED_SECTION_TEMPLATES``; used by Stage 8.2 (alias of ``REQUIRED_SECTIONS``).
SECTION_ORDER_EXPECTED: tuple[str, ...] = REQUIRED_SECTIONS

# Lowercase titles that often denote structural blocks (intro, bibliography, etc.).
SECTION_KEYWORDS_FOR_HEADING_DETECTION: frozenset[str] = frozenset(
    {
        "введение",
        "заключение",
        "содержание",
        "список литературы",
        "приложения",
    }
)

# Same set by default; split later if "special" semantics diverge from detection keywords.
KNOWN_SPECIAL_SECTIONS: frozenset[str] = SECTION_KEYWORDS_FOR_HEADING_DETECTION
