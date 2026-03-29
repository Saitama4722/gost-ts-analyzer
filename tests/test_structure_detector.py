"""Tests for Stage 6.1 structure detection (rule-based headings)."""

from backend.app.structure_detector import detect_structure


def test_numbered_headings_single_digit_dot() -> None:
    blocks = [
        "1. Введение",
        "Some body text.",
        "2. Основная часть",
        "More text.",
    ]
    out = detect_structure(blocks)["sections"]
    assert out == [
        {"title": "1. Введение", "start_block": 0},
        {"title": "2. Основная часть", "start_block": 2},
    ]


def test_numbered_headings_multi_level() -> None:
    blocks = [
        "1.1 Подраздел",
        "Paragraph.",
        "2.3.4 Глубокая нумерация",
    ]
    out = detect_structure(blocks)["sections"]
    assert out == [
        {"title": "1.1 Подраздел", "start_block": 0},
        {"title": "2.3.4 Глубокая нумерация", "start_block": 2},
    ]


def test_numbered_uses_first_line_of_block() -> None:
    blocks = ["1. Заголовок\nдоп. строка в блоке"]
    out = detect_structure(blocks)["sections"]
    assert out == [{"title": "1. Заголовок", "start_block": 0}]


def test_uppercase_headings() -> None:
    blocks = [
        "ВВЕДЕНИЕ",
        "Текст введения.",
        "ЗАКЛЮЧЕНИЕ",
        "Итоги.",
    ]
    out = detect_structure(blocks)["sections"]
    assert out == [
        {"title": "ВВЕДЕНИЕ", "start_block": 0},
        {"title": "ЗАКЛЮЧЕНИЕ", "start_block": 2},
    ]


def test_uppercase_spisok_literatury() -> None:
    blocks = ["СПИСОК ЛИТЕРАТУРЫ"]
    out = detect_structure(blocks)["sections"]
    assert out == [{"title": "СПИСОК ЛИТЕРАТУРЫ", "start_block": 0}]


def test_keyword_headings_case_insensitive() -> None:
    blocks = [
        "Введение",
        "Содержание",
        "список литературы",
        "Приложения",
    ]
    out = detect_structure(blocks)["sections"]
    assert len(out) == 4
    assert out[0] == {"title": "Введение", "start_block": 0}
    assert out[1] == {"title": "Содержание", "start_block": 1}
    assert out[2] == {"title": "список литературы", "start_block": 2}
    assert out[3] == {"title": "Приложения", "start_block": 3}


def test_no_false_positive_normal_sentences() -> None:
    blocks = [
        "Это обычный абзац с текстом на русском языке.",
        "Another paragraph in mixed Case and length.",
        "1.5 мм — размер, не раздел.",
        "Введение в тему данной работы не является заголовком раздела.",
        "123",
        "",
        "   ",
    ]
    out = detect_structure(blocks)["sections"]
    assert out == []


def test_uppercase_not_triggered_when_too_long() -> None:
    long_caps = "А" * 120
    blocks = [long_caps]
    assert detect_structure(blocks)["sections"] == []


def test_empty_blocks_ignored() -> None:
    blocks = ["", "  ", "1. Раздел"]
    out = detect_structure(blocks)["sections"]
    assert out == [{"title": "1. Раздел", "start_block": 2}]


def test_zaklyuchenie_keyword() -> None:
    blocks = ["заключение"]
    out = detect_structure(blocks)["sections"]
    assert out == [{"title": "заключение", "start_block": 0}]
