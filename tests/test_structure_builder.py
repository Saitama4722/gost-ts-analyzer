"""Tests for Stage 6.2 — hierarchical section tree from flat sections."""

from backend.app.structure_builder import (
    add_section_tree,
    build_section_tree,
    section_level_from_title,
)


def test_level_numbered_single_part() -> None:
    assert section_level_from_title("1. Введение") == 1
    assert section_level_from_title("1. ") == 1
    assert section_level_from_title("12. Заголовок") == 1


def test_level_numbered_two_parts() -> None:
    assert section_level_from_title("1.1 Подраздел") == 2
    assert section_level_from_title("2.3 Название") == 2


def test_level_numbered_three_parts() -> None:
    assert section_level_from_title("1.1.1 Пункт") == 3
    assert section_level_from_title("2.3.4 Глубокая нумерация") == 3


def test_level_non_numbered() -> None:
    assert section_level_from_title("ВВЕДЕНИЕ") == 1
    assert section_level_from_title("ЗАКЛЮЧЕНИЕ") == 1
    assert section_level_from_title("Введение") == 1


def test_simple_hierarchy() -> None:
    sections = [
        {"title": "1 Раздел", "start_block": 0},
        {"title": "1.1 Подраздел", "start_block": 3},
        {"title": "1.2 Подраздел", "start_block": 6},
        {"title": "2 Раздел", "start_block": 10},
    ]
    tree = build_section_tree(sections)
    assert len(tree) == 2
    assert tree[0]["title"] == "1 Раздел"
    assert tree[0]["level"] == 1
    assert len(tree[0]["children"]) == 2
    assert tree[0]["children"][0]["title"] == "1.1 Подраздел"
    assert tree[0]["children"][0]["level"] == 2
    assert tree[0]["children"][1]["title"] == "1.2 Подраздел"
    assert tree[1]["title"] == "2 Раздел"
    assert tree[1]["children"] == []


def test_deep_nesting() -> None:
    sections = [
        {"title": "1 Раздел", "start_block": 0},
        {"title": "1.1 Подраздел", "start_block": 1},
        {"title": "1.1.1 Пункт", "start_block": 2},
    ]
    tree = build_section_tree(sections)
    assert len(tree) == 1
    c1 = tree[0]["children"][0]
    assert c1["level"] == 2
    assert len(c1["children"]) == 1
    assert c1["children"][0]["title"] == "1.1.1 Пункт"
    assert c1["children"][0]["level"] == 3


def test_switching_levels_after_subsections() -> None:
    sections = [
        {"title": "1 А", "start_block": 0},
        {"title": "1.1 Б", "start_block": 1},
        {"title": "2 В", "start_block": 2},
    ]
    tree = build_section_tree(sections)
    assert len(tree) == 2
    assert tree[0]["children"][0]["title"] == "1.1 Б"
    assert tree[1]["title"] == "2 В"
    assert tree[1]["children"] == []


def test_non_numbered_flat_all_level_one_siblings() -> None:
    sections = [
        {"title": "ВВЕДЕНИЕ", "start_block": 0},
        {"title": "ЗАКЛЮЧЕНИЕ", "start_block": 2},
    ]
    tree = build_section_tree(sections)
    assert len(tree) == 2
    assert tree[0]["level"] == 1 and tree[1]["level"] == 1
    assert tree[0]["children"] == [] and tree[1]["children"] == []


def test_mixed_numbered_and_non_numbered() -> None:
    sections = [
        {"title": "ВВЕДЕНИЕ", "start_block": 0},
        {"title": "1. Основная часть", "start_block": 2},
        {"title": "1.1 Подраздел", "start_block": 4},
        {"title": "ЗАКЛЮЧЕНИЕ", "start_block": 8},
    ]
    tree = build_section_tree(sections)
    assert len(tree) == 3
    assert tree[0]["title"] == "ВВЕДЕНИЕ"
    assert tree[1]["title"] == "1. Основная часть"
    assert len(tree[1]["children"]) == 1
    assert tree[1]["children"][0]["title"] == "1.1 Подраздел"
    assert tree[2]["title"] == "ЗАКЛЮЧЕНИЕ"


def test_add_section_tree_preserves_sections_and_adds_tree() -> None:
    structure = {
        "sections": [
            {"title": "1. А", "start_block": 0},
            {"title": "1.1 Б", "start_block": 1},
        ]
    }
    out = add_section_tree(structure)
    assert out["sections"] == structure["sections"]
    assert "tree" in out
    assert len(out["tree"]) == 1
    assert len(out["tree"][0]["children"]) == 1
