"""Tests for Stage 13.4 issue_code → recommendation mapping."""



from __future__ import annotations



from backend.app.reporting.recommendations import recommendation_for_issue_code





def test_recommendation_exact_codes() -> None:

    assert recommendation_for_issue_code("unverifiable.obligation_without_metrics") == (

        "Добавьте числовой критерий, диапазон или единицу измерения."

    )

    assert recommendation_for_issue_code("figure.missing_declaration") == (

        "Добавьте подпись для указанного рисунка или исправьте ссылку на него."

    )

    assert recommendation_for_issue_code("duplicate.exact") == (

        "Удалите повтор или объедините дублирующие формулировки."

    )





def test_recommendation_prefix_codes() -> None:

    assert recommendation_for_issue_code("vague_wording.dictionary_phrase") == (

        "Уточните формулировку и замените расплывчатое слово на измеримый критерий."

    )

    assert recommendation_for_issue_code("terminology.mixed_variants.foo") == (

        "Используйте один вариант термина во всём документе."

    )

    assert recommendation_for_issue_code("required_sections.missing.introduction") is not None

    assert recommendation_for_issue_code("content.purpose_missing") is not None

    assert recommendation_for_issue_code("appendix.missing_declaration.А") is not None





def test_recommendation_unmapped_and_blank() -> None:

    assert recommendation_for_issue_code("future.unknown_code") is None

    assert recommendation_for_issue_code("") is None

    assert recommendation_for_issue_code("   ") is None


