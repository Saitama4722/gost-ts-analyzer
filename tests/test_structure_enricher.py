"""Tests for Stage 6.3 — section boundaries and body extraction."""

from backend.app.structure_builder import add_section_tree
from backend.app.structure_enricher import enrich_structure


def _enrich_from_sections(sections: list[dict], blocks: list[str]) -> dict:
    base = add_section_tree({"sections": sections})
    return enrich_structure(base, blocks)


def test_simple_two_sections_flat_and_tree() -> None:
    blocks = ["1. First", "body1", "2. Second", "a", "b"]
    sections = [
        {"title": "1. First", "start_block": 0},
        {"title": "2. Second", "start_block": 2},
    ]
    out = _enrich_from_sections(sections, blocks)
    s0, s1 = out["sections"]
    assert s0["start_block"] == 0 and s0["end_block"] == 1
    assert s0["content_blocks"] == ["1. First", "body1"]
    assert s0["content_text"] == "1. First\nbody1"
    assert s1["start_block"] == 2 and s1["end_block"] == 4
    assert s1["content_blocks"] == ["2. Second", "a", "b"]
    assert len(out["tree"]) == 2
    t0, t1 = out["tree"]
    assert t0["end_block"] == 1 and t1["end_block"] == 4


def test_nested_parent_excludes_child_blocks_in_tree() -> None:
    blocks = ["1. A", "text A", "1.1 B", "text B", "2. C"]
    sections = [
        {"title": "1. A", "start_block": 0},
        {"title": "1.1 B", "start_block": 2},
        {"title": "2. C", "start_block": 4},
    ]
    out = _enrich_from_sections(sections, blocks)
    root = out["tree"][0]
    assert root["end_block"] == 3
    assert root["content_blocks"] == ["1. A", "text A"]
    assert root["content_text"] == "1. A\ntext A"
    child = root["children"][0]
    assert child["start_block"] == 2 and child["end_block"] == 3
    assert child["content_blocks"] == ["1.1 B", "text B"]
    assert child["content_text"] == "1.1 B\ntext B"
    s0, s1, s2 = out["sections"]
    assert s0["end_block"] == 1
    assert s0["content_text"] == "1. A\ntext A"
    assert s1["end_block"] == 3
    assert s1["content_text"] == "1.1 B\ntext B"
    assert s2["end_block"] == 4
    assert s2["content_text"] == "2. C"


def test_last_section_spans_to_end_of_blocks() -> None:
    blocks = ["1. A", "x", "y", "2. B", "tail1", "tail2", "tail3"]
    sections = [
        {"title": "1. A", "start_block": 0},
        {"title": "2. B", "start_block": 3},
    ]
    out = _enrich_from_sections(sections, blocks)
    last = out["sections"][-1]
    assert last["end_block"] == len(blocks) - 1 == 6
    assert last["content_blocks"] == ["2. B", "tail1", "tail2", "tail3"]


def test_no_sections() -> None:
    out = enrich_structure({"sections": [], "tree": []}, ["a", "b"])
    assert out["sections"] == []
    assert out["tree"] == []


def test_single_section() -> None:
    blocks = ["1. Only", "p1", "p2"]
    sections = [{"title": "1. Only", "start_block": 0}]
    out = _enrich_from_sections(sections, blocks)
    s = out["sections"][0]
    assert s["end_block"] == 2
    assert s["content_blocks"] == blocks
    assert s["content_text"] == "1. Only\np1\np2"
    t = out["tree"][0]
    assert t["end_block"] == 2
    assert t["content_blocks"] == blocks


def test_tree_multiple_children_ranges_excluded() -> None:
    blocks = [
        "1. R",
        "intro",
        "1.1 A",
        "a body",
        "1.2 B",
        "b body",
        "2. Next",
    ]
    sections = [
        {"title": "1. R", "start_block": 0},
        {"title": "1.1 A", "start_block": 2},
        {"title": "1.2 B", "start_block": 4},
        {"title": "2. Next", "start_block": 6},
    ]
    out = _enrich_from_sections(sections, blocks)
    root = out["tree"][0]
    assert root["end_block"] == 5
    assert root["content_text"] == "1. R\nintro"
    assert root["children"][0]["content_text"] == "1.1 A\na body"
    assert root["children"][1]["content_text"] == "1.2 B\nb body"


def test_enrich_copies_structure_does_not_mutate_input() -> None:
    sections = [{"title": "1. A", "start_block": 0}]
    base = add_section_tree({"sections": sections})
    base_copy_sections = [dict(s) for s in base["sections"]]
    enrich_structure(base, ["x"])
    assert base["sections"] == base_copy_sections
    assert "end_block" not in base["sections"][0]
