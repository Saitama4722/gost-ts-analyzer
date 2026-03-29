"""Deterministic Russian correction hints keyed by ``issue_code`` (Stage 13.4).

Prefixes cover dynamic suffixes such as ``vague_wording.<match_type>`` and
``terminology.mixed_variants.<term_key>`` produced by the issues builder.
"""

from __future__ import annotations

# Exact codes emitted by ``issues_builder`` (figure, unverifiable, duplicates).
_ISSUE_CODE_TO_RECOMMENDATION: dict[str, str] = {
    "section_order.violation": (
        "Расположите обязательные разделы в порядке, соответствующем типовой структуре ТЗ."
    ),
    "numerical.missing_in_obligation_fragment": (
        "Укажите измеримый показатель: число, диапазон, допуск или единицу измерения."
    ),
    "measurement.unit_linkage_review": (
        "Явно свяжите числовое значение с единицей измерения в одной фразе требования."
    ),
    "table.missing_declaration": (
        "Добавьте строку объявления таблицы с номером или исправьте ссылку на таблицу."
    ),
    "table.unreferenced": (
        "Добавьте упоминание таблицы в тексте или удалите лишнее объявление."
    ),
    "table.duplicate_declaration": (
        "Оставьте одно объявление для номера таблицы или устраните дублирование."
    ),
    "table.caption_numbering_gap": (
        "Восстановите непрерывную нумерацию таблиц или исправьте пропуск в нумерации."
    ),
    "unverifiable.obligation_without_metrics": (
        "Добавьте числовой критерий, диапазон или единицу измерения."
    ),
    "figure.missing_declaration": (
        "Добавьте подпись для указанного рисунка или исправьте ссылку на него."
    ),
    "figure.unreferenced": (
        "Добавьте упоминание рисунка в тексте или удалите лишнюю подпись."
    ),
    "figure.duplicate_declaration": (
        "Оставьте одну подпись для номера рисунка или устраните дублирование."
    ),
    "figure.caption_numbering_gap": (
        "Восстановите непрерывную нумерацию подписей к рисункам или исправьте пропуск."
    ),
    "duplicate.exact": "Удалите повтор или объедините дублирующие формулировки.",
    "duplicate.near": "Удалите повтор или объедините дублирующие формулировки.",
}

_VAGUE_WORDING_PREFIX = "vague_wording."
_TERMINOLOGY_MIXED_PREFIX = "terminology.mixed_variants."
_REQUIRED_SECTIONS_MISSING_PREFIX = "required_sections.missing."
_CONTENT_PRESENCE_PREFIX = "content."
_APPENDIX_MISSING_DECL_PREFIX = "appendix.missing_declaration."
_APPENDIX_UNREF_PREFIX = "appendix.unreferenced."
_APPENDIX_DUP_PREFIX = "appendix.duplicate_declaration."
_APPENDIX_CYR_GAP_PREFIX = "appendix.cyrillic_sequence_gap."
_APPENDIX_NUM_GAP_PREFIX = "appendix.numeric_sequence_gap."

_REC_VAGUE_WORDING = (
    "Уточните формулировку и замените расплывчатое слово на измеримый критерий."
)
_REC_TERMINOLOGY = "Используйте один вариант термина во всём документе."
_REC_REQUIRED_SECTION = (
    "Добавьте раздел с указанным заголовком или допустимым вариантом из шаблона структуры."
)
_REC_CONTENT_PRESENCE = (
    "Добавьте соответствующий раздел или явную формулировку в тексте документа."
)
_REC_APPENDIX_MISSING = (
    "Добавьте строку объявления приложения или исправьте ссылку на обозначение."
)
_REC_APPENDIX_UNREF = (
    "Добавьте упоминание приложения в тексте или удалите лишнее объявление."
)
_REC_APPENDIX_DUP = "Оставьте одно объявление для обозначения приложения."
_REC_APPENDIX_GAP = "Восстановите непрерывную нумерацию или последовательность обозначений приложений."


def recommendation_for_issue_code(issue_code: str) -> str | None:
    """Return a short Russian hint for a known ``issue_code``, else ``None``."""
    code = str(issue_code).strip()
    if not code:
        return None
    if code in _ISSUE_CODE_TO_RECOMMENDATION:
        return _ISSUE_CODE_TO_RECOMMENDATION[code]
    if code.startswith(_VAGUE_WORDING_PREFIX):
        return _REC_VAGUE_WORDING
    if code.startswith(_TERMINOLOGY_MIXED_PREFIX):
        return _REC_TERMINOLOGY
    if code.startswith(_REQUIRED_SECTIONS_MISSING_PREFIX):
        return _REC_REQUIRED_SECTION
    if code.startswith(_CONTENT_PRESENCE_PREFIX):
        return _REC_CONTENT_PRESENCE
    if code.startswith(_APPENDIX_MISSING_DECL_PREFIX):
        return _REC_APPENDIX_MISSING
    if code.startswith(_APPENDIX_UNREF_PREFIX):
        return _REC_APPENDIX_UNREF
    if code.startswith(_APPENDIX_DUP_PREFIX):
        return _REC_APPENDIX_DUP
    if code.startswith(_APPENDIX_CYR_GAP_PREFIX) or code.startswith(_APPENDIX_NUM_GAP_PREFIX):
        return _REC_APPENDIX_GAP
    return None
