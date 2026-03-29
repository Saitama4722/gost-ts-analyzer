"""Stage 6.3: attach block ranges and section body content for rule-based analysis.

Deterministic index-only logic: ``blocks`` are the only content source.
Does not modify detection (6.1) or tree shape (6.2).
"""

from __future__ import annotations

from typing import Any


def _enrich_flat_section(
    sections: list[dict[str, Any]],
    blocks: list[str],
    index: int,
) -> dict[str, Any]:
    sec = sections[index]
    start = int(sec["start_block"])
    if index + 1 < len(sections):
        end = int(sections[index + 1]["start_block"]) - 1
    else:
        end = len(blocks) - 1 if blocks else -1

    content_blocks: list[str] = []
    if blocks and start <= end:
        hi = min(end, len(blocks) - 1)
        lo = min(max(0, start), hi)
        content_blocks = blocks[lo : hi + 1]

    out = dict(sec)
    out["start_block"] = start
    out["end_block"] = end
    out["content_blocks"] = content_blocks
    out["content_text"] = "\n".join(content_blocks)
    return out


def _enrich_tree_node(
    node: dict[str, Any],
    sections: list[dict[str, Any]],
    blocks: list[str],
    flat_idx: int,
) -> tuple[dict[str, Any], int]:
    j = flat_idx + 1
    enriched_children: list[dict[str, Any]] = []
    for ch in node.get("children") or []:
        ech, j = _enrich_tree_node(ch, sections, blocks, j)
        enriched_children.append(ech)

    start = int(node["start_block"])
    last_subtree = j - 1
    next_flat = last_subtree + 1
    if next_flat < len(sections):
        end = int(sections[next_flat]["start_block"]) - 1
    else:
        end = len(blocks) - 1 if blocks else -1

    excluded_ranges: list[tuple[int, int]] = [
        (int(c["start_block"]), int(c["end_block"])) for c in enriched_children
    ]

    content_blocks: list[str] = []
    if blocks and start <= end:
        hi = min(end, len(blocks) - 1)
        for bi in range(max(0, start), hi + 1):
            if any(cs <= bi <= ce for cs, ce in excluded_ranges):
                continue
            content_blocks.append(blocks[bi])

    out = dict(node)
    out["start_block"] = start
    out["end_block"] = end
    out["content_blocks"] = content_blocks
    out["content_text"] = "\n".join(content_blocks)
    out["children"] = enriched_children
    return out, j


def _enrich_tree_forest(
    tree: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    blocks: list[str],
) -> list[dict[str, Any]]:
    idx = 0
    out: list[dict[str, Any]] = []
    for node in tree:
        en, idx = _enrich_tree_node(node, sections, blocks, idx)
        out.append(en)
    return out


def enrich_structure(structure: dict[str, Any], blocks: list[str]) -> dict[str, Any]:
    """Return a copy of ``structure`` with ``end_block``, ``content_blocks``, ``content_text``.

    Flat ``sections`` use the next section in list order for ``end_block`` and a contiguous
    block slice for body text (no subtree overlap in that range).

    ``tree`` nodes use subtree extent for ``end_block`` and exclude direct children's block
    ranges from ``content_blocks``.
    """
    sections = structure.get("sections", [])
    if not isinstance(sections, list):
        sections = []
    tree = structure.get("tree", [])
    if not isinstance(tree, list):
        tree = []

    blocks_list = list(blocks)
    enriched_sections = [_enrich_flat_section(sections, blocks_list, i) for i in range(len(sections))]
    enriched_tree = _enrich_tree_forest(tree, sections, blocks_list)

    out = dict(structure)
    out["sections"] = enriched_sections
    out["tree"] = enriched_tree
    return out
