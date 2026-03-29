"""Small shared helpers for caption/mention number sets (figures, tables, etc.)."""

from __future__ import annotations


def sorted_unique_ints(nums: set[int]) -> list[int]:
    return sorted(nums)


def numbering_gaps_in_range(declared: set[int]) -> list[int]:
    if not declared:
        return []
    lo, hi = min(declared), max(declared)
    return [n for n in range(lo, hi + 1) if n not in declared]
