"""Shared rule constants: heading heuristics and placeholders for later checks.

Stage 7.1: storage only. Patterns are consumed by structure detection (6.1) and
tree building (6.2). Stage 7.3: ``FORBIDDEN_VAGUE_PHRASES`` — vague wording
dictionary (consumed by Stage 10.1 ``vague_wording_check``; defined only here).
Stage 7.4:
``GLOSSARY_CANONICAL_TERMS`` — canonical Russian terms and aliases for future
terminology consistency checks; no matching or validation logic here.
"""

from __future__ import annotations

import re
from typing import Final, TypedDict

# --- Numbered heading patterns (first line of block) ---
# "1. Title" — space after the first dot (not "1.5 мм" via two-part + measurement filter).
NUMBERED_HEADING_DOT_PATTERN = re.compile(r"^\d+\.\s+")
# "2.3.4 Title" — at least two ".N" segments after the leading number.
NUMBERED_HEADING_DEEP_PATTERN = re.compile(r"^\d+(\.\d+){2,}\s+")
# "1.1 Title" — two numeric segments; measurement filter excludes lines like "1.5 мм".
NUMBERED_HEADING_TWO_PART_PATTERN = re.compile(r"^\d+\.\d+\s+")

# First token after "N.N " that indicates a measurement, not a subsection title.
MEASUREMENT_FIRST_TOKENS: frozenset[str] = frozenset(
    {
        "мм",
        "см",
        "дм",
        "м",
        "км",
        "г",
        "кг",
        "мг",
        "с",
        "мин",
        "ч",
        "%",
    }
)

# Whole-block ALL-CAPS heading: ignore very long blocks (likely tables or noise).
MAX_UPPERCASE_HEADING_BLOCK_LEN = 120

# Leading numeric index from a title line (for tree level in 6.2).
NUMERIC_TITLE_PREFIX_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)")

class GlossaryTermEntry(TypedDict):
    """One canonical term with variants for future glossary-based analysis.

    * ``key`` — stable English identifier for code.
    * ``canonical`` — preferred Russian form (lowercase).
    * ``aliases`` — lowercase variants (abbreviations, spelling); must include
      ``canonical`` exactly once; no duplicates within the tuple.
    """

    key: str
    canonical: str
    aliases: tuple[str, ...]


class VaguePhraseEntry(TypedDict):
    """One vague or low-quality wording marker for future ТЗ text analysis.

    * ``phrase`` — normalized substring to match (lowercase, no trailing punctuation).
    * ``type`` — short category label (e.g. speed, filler).
    * ``description`` — why the wording is problematic (Russian, for humans / UI later).
    """

    phrase: str
    type: str
    description: str


# Vague / non-measurable wording — data only (Stage 7.3). Types: speed, usability,
# quality, abstraction, weak_verb, filler.
FORBIDDEN_VAGUE_PHRASES: Final[list[VaguePhraseEntry]] = [
    {
        "phrase": "быстро",
        "type": "speed",
        "description": "Не содержит измеримого критерия времени",
    },
    {
        "phrase": "быстрое выполнение",
        "type": "speed",
        "description": "Нужны сроки, метрики или допустимые задержки",
    },
    {
        "phrase": "высокая скорость",
        "type": "speed",
        "description": "Скорость должна быть количественно определена",
    },
    {
        "phrase": "в кратчайшие сроки",
        "type": "speed",
        "description": "Формулировка не измерима; задайте конкретные сроки",
    },
    {
        "phrase": "без задержек",
        "type": "speed",
        "description": "Требует уточнения допустимой задержки или режима работы",
    },
    {
        "phrase": "удобно",
        "type": "usability",
        "description": "Субъективно; опишите сценарии и критерии удобства",
    },
    {
        "phrase": "удобный интерфейс",
        "type": "usability",
        "description": "Нужны требования к составу экранов, доступности, ошибкам",
    },
    {
        "phrase": "интуитивно понятный",
        "type": "usability",
        "description": "Нельзя проверить без целевой аудитории и критериев обучения",
    },
    {
        "phrase": "простота использования",
        "type": "usability",
        "description": "Замените измеримыми показателями (время задачи, ошибки)",
    },
    {
        "phrase": "качественно",
        "type": "quality",
        "description": "Нужны критерии приёмки и метрики качества",
    },
    {
        "phrase": "надежно",
        "type": "quality",
        "description": "Без показателей надёжности формулировка не проверяема",
    },
    {
        "phrase": "надёжно",
        "type": "quality",
        "description": "Без показателей надёжности формулировка не проверяема",
    },
    {
        "phrase": "эффективно",
        "type": "quality",
        "description": "Уточните эффективность по какому показателю измеряется",
    },
    {
        "phrase": "достаточно",
        "type": "quality",
        "description": "Не определено, достаточно для чего и по каким нормам",
    },
    {
        "phrase": "возможность",
        "type": "abstraction",
        "description": "Абстрактное существительное без конкретных действий или объёмов",
    },
    {
        "phrase": "функциональность",
        "type": "abstraction",
        "description": "Перечислите функции и ограничения вместо общего термина",
    },
    {
        "phrase": "оптимизация",
        "type": "abstraction",
        "description": "Укажите что оптимизируется и целевые значения",
    },
    {
        "phrase": "должен обеспечивать возможность",
        "type": "weak_verb",
        "description": "Слабая формулировка; задайте обязательное действие или результат",
    },
    {
        "phrase": "предусмотреть возможность",
        "type": "weak_verb",
        "description": "Требование размыто; определите обязательность и условия",
    },
    {
        "phrase": "может использоваться",
        "type": "weak_verb",
        "description": "Не ясно обязательно ли использование и в каких случаях",
    },
    {
        "phrase": "следует обеспечить возможность",
        "type": "weak_verb",
        "description": "Замените на однозначное требование или критерий",
    },
    {
        "phrase": "при необходимости",
        "type": "filler",
        "description": "Условие не определено; укажите триггеры и обязанности",
    },
    {
        "phrase": "по возможности",
        "type": "filler",
        "description": "Снимает обязательность; зафиксируйте must/should или критерии",
    },
    {
        "phrase": "в случае необходимости",
        "type": "filler",
        "description": "Нужно описать случаи и обязательные действия",
    },
    {
        "phrase": "при наличии возможности",
        "type": "filler",
        "description": "Не проверяемо; определите условия и приоритет",
    },
]

# Canonical terminology — data only (Stage 7.4). Lowercase; matching later.
GLOSSARY_CANONICAL_TERMS: Final[list[GlossaryTermEntry]] = [
    {
        "key": "technical_specification",
        "canonical": "техническое задание",
        "aliases": (
            "техническое задание",
            "тз",
            "техническое требование",
        ),
    },
    {
        "key": "document",
        "canonical": "документ",
        "aliases": ("документ",),
    },
    {
        "key": "section",
        "canonical": "раздел",
        "aliases": ("раздел",),
    },
    {
        "key": "subsection",
        "canonical": "подраздел",
        "aliases": ("подраздел", "подпункт"),
    },
    {
        "key": "requirement",
        "canonical": "требование",
        "aliases": ("требование",),
    },
    {
        "key": "functional_requirement",
        "canonical": "функциональное требование",
        "aliases": (
            "функциональное требование",
            "функциональные требования",
        ),
    },
    {
        "key": "nonfunctional_requirement",
        "canonical": "нефункциональное требование",
        "aliases": (
            "нефункциональное требование",
            "нефункциональные требования",
        ),
    },
    {
        "key": "acceptance_criterion",
        "canonical": "критерий приёмки",
        "aliases": (
            "критерий приёмки",
            "критерий приемки",
            "критерии приёмки",
            "критерии приемки",
        ),
    },
    {
        "key": "appendix",
        "canonical": "приложение",
        "aliases": ("приложение", "приложения"),
    },
    {
        "key": "table",
        "canonical": "таблица",
        "aliases": ("таблица", "табл."),
    },
    {
        "key": "figure",
        "canonical": "рисунок",
        "aliases": ("рисунок", "рис."),
    },
    {
        "key": "interface",
        "canonical": "интерфейс",
        "aliases": ("интерфейс", "пользовательский интерфейс"),
    },
    {
        "key": "performance",
        "canonical": "производительность",
        "aliases": ("производительность", "быстродействие"),
    },
    {
        "key": "reliability",
        "canonical": "надёжность",
        "aliases": ("надёжность", "надежность"),
    },
    {
        "key": "security",
        "canonical": "безопасность",
        "aliases": ("безопасность", "информационная безопасность"),
    },
]
