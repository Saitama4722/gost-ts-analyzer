"""Aggregate supported raw check results into a flat list of ``Issue`` records (Stages 13.3–13.4).

Raw ``checks`` in API responses stay unchanged. Stage 13.4 attaches deterministic
``recommendation`` text. Adapters cover structural checks, content-presence checks,
wording/quality-related checks, numerical/measurement fragments, reference consistency,
terminology, and duplicates.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from backend.app.reporting.issue_model import (
    Issue,
    IssueLocation,
    issue_from_vague_wording_finding,
    issue_to_dict,
    make_issue,
    make_issue_location,
)
from backend.app.reporting.recommendations import recommendation_for_issue_code
from backend.app.rules.section_rules import REQUIRED_SECTION_TEMPLATES


def _as_mapping(obj: object) -> Mapping[str, Any]:
    return obj if isinstance(obj, Mapping) else {}


def _issues_from_vague_wording(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("vague_wording_check"))
    raw = block.get("findings")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(issue_from_vague_wording_finding(item))
    return out


def _issues_from_unverifiable_requirements(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("unverifiable_requirements_check"))
    raw = block.get("items")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        reason = str(item.get("reason") or "").strip()
        message = reason if reason else "Обнаружена формулировка требования без измеримых критериев."
        st = item.get("section_title")
        section_title = str(st).strip() if st is not None else None
        section_out = section_title if section_title else None
        meta = {
            k: item[k]
            for k in ("obligation_marker", "reason", "fragment_index")
            if k in item
        }
        fi = item.get("fragment_index")
        locations = None
        if isinstance(fi, int):
            locations = (make_issue_location(fragment_index=fi),)
        out.append(
            make_issue(
                check_key="unverifiable_requirements_check",
                issue_code="unverifiable.obligation_without_metrics",
                message=message,
                fragment_text=text if text else None,
                section_title=section_out,
                metadata=meta,
                severity="warning",
                locations=locations,
            )
        )
    return out


def _required_section_title_for_key(key: str) -> str:
    for tpl in REQUIRED_SECTION_TEMPLATES:
        if str(tpl["key"]) == key:
            return str(tpl["title"])
    return key


def _issues_from_required_sections(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("required_sections_check"))
    raw = block.get("missing")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        key = str(item).strip()
        if not key:
            continue
        title = _required_section_title_for_key(key)
        out.append(
            make_issue(
                check_key="required_sections_check",
                issue_code=f"required_sections.missing.{key}",
                message=f"Отсутствует обязательный раздел: «{title}».",
                metadata={"section_key": key, "canonical_title": title},
                severity="warning",
            )
        )
    return out


def _issues_from_section_order(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("section_order_check"))
    if block.get("is_correct") is not False:
        return []
    violations = block.get("violations")
    if not isinstance(violations, list):
        return []
    out: list[Issue] = []
    for v in violations:
        if not isinstance(v, dict):
            continue
        exp_k = str(v.get("expected_key") or "").strip()
        got_k = str(v.get("found_key") or "").strip()
        if not exp_k or not got_k:
            continue
        exp_t = _required_section_title_for_key(exp_k)
        got_t = _required_section_title_for_key(got_k)
        out.append(
            make_issue(
                check_key="section_order_check",
                issue_code="section_order.violation",
                message=(
                    f"Нарушен ожидаемый порядок разделов: после «{exp_t}» ожидался "
                    f"фрагмент структуры, фактически обнаружен раздел «{got_t}»."
                ),
                metadata={
                    "expected_key": exp_k,
                    "found_key": got_k,
                    "index": v.get("index"),
                },
                severity="warning",
            )
        )
    return out


def _issues_from_presence_checks(checks: Mapping[str, Any]) -> list[Issue]:
    specs: tuple[tuple[str, str, str, str], ...] = (
        (
            "purpose_check",
            "content.purpose_missing",
            "Не обнаружены явные признаки раздела или формулировок цели / назначения документа.",
        ),
        (
            "scope_check",
            "content.scope_missing",
            "Не обнаружены явные признаки раздела или формулировок области применения.",
        ),
        (
            "functional_requirements_check",
            "content.functional_requirements_missing",
            "Не обнаружены явные признаки раздела или формулировок функциональных требований.",
        ),
        (
            "nonfunctional_requirements_check",
            "content.nonfunctional_requirements_missing",
            "Не обнаружены явные признаки раздела или формулировок нефункциональных требований.",
        ),
        (
            "acceptance_criteria_check",
            "content.acceptance_criteria_missing",
            "Не обнаружены явные признаки раздела или формулировок критериев приёмки.",
        ),
    )
    out: list[Issue] = []
    for check_key, code, message in specs:
        block = _as_mapping(checks.get(check_key))
        if block.get("is_present") is not False:
            continue
        out.append(
            make_issue(
                check_key=check_key,
                issue_code=code,
                message=message,
                severity="warning",
            )
        )
    return out


def _issues_from_numerical_characteristics(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("numerical_characteristics_check"))
    raw = block.get("items")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if item.get("has_numeric_characteristics") is True:
            continue
        text = str(item.get("text") or "").strip()
        st = item.get("section_title")
        section_title = str(st).strip() if st is not None else None
        section_out = section_title if section_title else None
        fi = item.get("fragment_index")
        locs: tuple[IssueLocation, ...] | None = None
        if isinstance(fi, int):
            locs = (make_issue_location(fragment_index=fi),)
        meta = {k: item[k] for k in ("fragment_index", "matched_signals") if k in item}
        out.append(
            make_issue(
                check_key="numerical_characteristics_check",
                issue_code="numerical.missing_in_obligation_fragment",
                message=(
                    "В формулировке требования не обнаружены числовые характеристики "
                    "(проценты, диапазоны, единицы и т.п.)."
                ),
                fragment_text=text if text else None,
                section_title=section_out,
                metadata=meta,
                severity="recommendation",
                locations=locs,
            )
        )
    return out


def _measurement_fragment_needs_issue(item: Mapping[str, Any]) -> bool:
    if item.get("number_unit_linked") is True:
        return False
    return bool(item.get("has_numeric_value")) or bool(item.get("has_unit"))


def _issues_from_measurement_units(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("measurement_units_check"))
    raw = block.get("items")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if not _measurement_fragment_needs_issue(item):
            continue
        text = str(item.get("text") or "").strip()
        reason = str(item.get("reason") or "").strip()
        message = reason if reason else "Требуется проверить связь числа и единицы измерения."
        st = item.get("section_title")
        section_title = str(st).strip() if st is not None else None
        section_out = section_title if section_title else None
        fi = item.get("fragment_index")
        locs: tuple[IssueLocation, ...] | None = None
        if isinstance(fi, int):
            locs = (make_issue_location(fragment_index=fi),)
        meta = {
            k: item[k]
            for k in (
                "has_numeric_value",
                "has_unit",
                "number_unit_linked",
                "matched_units",
                "reason",
                "matched_signal_categories",
                "fragment_index",
            )
            if k in item
        }
        out.append(
            make_issue(
                check_key="measurement_units_check",
                issue_code="measurement.unit_linkage_review",
                message=message,
                fragment_text=text if text else None,
                section_title=section_out,
                metadata=meta,
                severity="recommendation",
                locations=locs,
            )
        )
    return out


def _first_figure_mention_locations(
    block: Mapping[str, Any], number: int
) -> tuple[IssueLocation, ...] | None:
    mentions = block.get("mentions")
    if not isinstance(mentions, list):
        return None
    for m in mentions:
        if not isinstance(m, dict):
            continue
        if m.get("number") != number:
            continue
        bi, li = m.get("block_index"), m.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _first_figure_declaration_locations(
    block: Mapping[str, Any], number: int
) -> tuple[IssueLocation, ...] | None:
    decls = block.get("declarations")
    if not isinstance(decls, list):
        return None
    for d in decls:
        if not isinstance(d, dict):
            continue
        if d.get("number") != number:
            continue
        bi, li = d.get("block_index"), d.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _issues_from_figure_references(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("figure_references_check"))
    out: list[Issue] = []

    for num in block.get("missing_declarations") or []:
        if not isinstance(num, int):
            continue
        locs = _first_figure_mention_locations(block, num)
        out.append(
            make_issue(
                check_key="figure_references_check",
                issue_code="figure.missing_declaration",
                message=(
                    f"Упоминается рисунок {num}, но строка объявления рисунка "
                    "(подпись) с этим номером не найдена."
                ),
                metadata={"figure_number": num},
                severity="warning",
                locations=locs,
            )
        )

    for num in block.get("unreferenced_figures") or []:
        if not isinstance(num, int):
            continue
        locs = _first_figure_declaration_locations(block, num)
        out.append(
            make_issue(
                check_key="figure_references_check",
                issue_code="figure.unreferenced",
                message=(
                    f"Объявлен рисунок {num}, но в тексте не найдено упоминание "
                    "этого номера."
                ),
                metadata={"figure_number": num},
                severity="warning",
                locations=locs,
            )
        )

    for num in block.get("duplicate_declarations") or []:
        if not isinstance(num, int):
            continue
        out.append(
            make_issue(
                check_key="figure_references_check",
                issue_code="figure.duplicate_declaration",
                message=f"Рисунок {num} объявлен (подписан) более одного раза.",
                metadata={"figure_number": num},
                severity="warning",
            )
        )

    for num in block.get("caption_numbering_gaps") or []:
        if not isinstance(num, int):
            continue
        out.append(
            make_issue(
                check_key="figure_references_check",
                issue_code="figure.caption_numbering_gap",
                message=(
                    f"В последовательности номеров подписей к рисункам пропущен номер {num}."
                ),
                metadata={"missing_number": num},
                severity="recommendation",
            )
        )

    return out


def _first_table_mention_locations(
    block: Mapping[str, Any], number: int
) -> tuple[IssueLocation, ...] | None:
    mentions = block.get("mentions")
    if not isinstance(mentions, list):
        return None
    for m in mentions:
        if not isinstance(m, dict):
            continue
        if m.get("number") != number:
            continue
        bi, li = m.get("block_index"), m.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _first_table_declaration_locations(
    block: Mapping[str, Any], number: int
) -> tuple[IssueLocation, ...] | None:
    decls = block.get("declarations")
    if not isinstance(decls, list):
        return None
    for d in decls:
        if not isinstance(d, dict):
            continue
        if d.get("number") != number:
            continue
        bi, li = d.get("block_index"), d.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _issues_from_table_references(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("table_references_check"))
    out: list[Issue] = []

    for num in block.get("missing_declarations") or []:
        if not isinstance(num, int):
            continue
        locs = _first_table_mention_locations(block, num)
        out.append(
            make_issue(
                check_key="table_references_check",
                issue_code="table.missing_declaration",
                message=(
                    f"Упоминается таблица {num}, но строка объявления таблицы "
                    "(заголовок) с этим номером не найдена."
                ),
                metadata={"table_number": num},
                severity="warning",
                locations=locs,
            )
        )

    for num in block.get("unreferenced_tables") or []:
        if not isinstance(num, int):
            continue
        locs = _first_table_declaration_locations(block, num)
        out.append(
            make_issue(
                check_key="table_references_check",
                issue_code="table.unreferenced",
                message=(
                    f"Объявлена таблица {num}, но в тексте не найдено упоминание "
                    "этого номера."
                ),
                metadata={"table_number": num},
                severity="warning",
                locations=locs,
            )
        )

    for num in block.get("duplicate_declarations") or []:
        if not isinstance(num, int):
            continue
        out.append(
            make_issue(
                check_key="table_references_check",
                issue_code="table.duplicate_declaration",
                message=f"Таблица {num} объявлена (подписана) более одного раза.",
                metadata={"table_number": num},
                severity="warning",
            )
        )

    for num in block.get("caption_numbering_gaps") or []:
        if not isinstance(num, int):
            continue
        out.append(
            make_issue(
                check_key="table_references_check",
                issue_code="table.caption_numbering_gap",
                message=(
                    f"В последовательности номеров подписей к таблицам пропущен номер {num}."
                ),
                metadata={"missing_number": num},
                severity="recommendation",
            )
        )

    return out


def _first_appendix_mention_locations(
    block: Mapping[str, Any], label: str
) -> tuple[IssueLocation, ...] | None:
    mentions = block.get("mentions")
    if not isinstance(mentions, list):
        return None
    for m in mentions:
        if not isinstance(m, dict):
            continue
        if str(m.get("label") or "") != label:
            continue
        bi, li = m.get("block_index"), m.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _first_appendix_declaration_locations(
    block: Mapping[str, Any], label: str
) -> tuple[IssueLocation, ...] | None:
    decls = block.get("declarations")
    if not isinstance(decls, list):
        return None
    for d in decls:
        if not isinstance(d, dict):
            continue
        if str(d.get("label") or "") != label:
            continue
        bi, li = d.get("block_index"), d.get("line_index")
        loc_bi = bi if isinstance(bi, int) else None
        loc_li = li if isinstance(li, int) else None
        if loc_bi is None and loc_li is None:
            continue
        return (make_issue_location(block_index=loc_bi, line_index=loc_li),)
    return None


def _issues_from_appendix_references(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("appendix_references_check"))
    out: list[Issue] = []

    for label in block.get("missing_declarations") or []:
        lab = str(label).strip()
        if not lab:
            continue
        locs = _first_appendix_mention_locations(block, lab)
        out.append(
            make_issue(
                check_key="appendix_references_check",
                issue_code=f"appendix.missing_declaration.{lab}",
                message=(
                    f"Упоминается приложение {lab}, но строка объявления приложения "
                    "с этим обозначением не найдена."
                ),
                metadata={"appendix_label": lab},
                severity="warning",
                locations=locs,
            )
        )

    for label in block.get("unreferenced_appendices") or []:
        lab = str(label).strip()
        if not lab:
            continue
        locs = _first_appendix_declaration_locations(block, lab)
        out.append(
            make_issue(
                check_key="appendix_references_check",
                issue_code=f"appendix.unreferenced.{lab}",
                message=(
                    f"Объявлено приложение {lab}, но в тексте не найдено соответствующее упоминание."
                ),
                metadata={"appendix_label": lab},
                severity="warning",
                locations=locs,
            )
        )

    for label in block.get("duplicate_declarations") or []:
        lab = str(label).strip()
        if not lab:
            continue
        out.append(
            make_issue(
                check_key="appendix_references_check",
                issue_code=f"appendix.duplicate_declaration.{lab}",
                message=f"Приложение {lab} объявлено более одного раза.",
                metadata={"appendix_label": lab},
                severity="warning",
            )
        )

    for letter in block.get("cyrillic_letter_sequence_gaps") or []:
        ch = str(letter).strip()
        if not ch:
            continue
        out.append(
            make_issue(
                check_key="appendix_references_check",
                issue_code=f"appendix.cyrillic_sequence_gap.{ch}",
                message=(
                    f"В последовательности обозначений приложений (кириллица) "
                    f"пропущена буква «{ch}»."
                ),
                metadata={"missing_letter": ch},
                severity="recommendation",
            )
        )

    for num in block.get("numeric_appendix_gaps") or []:
        if not isinstance(num, int):
            continue
        out.append(
            make_issue(
                check_key="appendix_references_check",
                issue_code=f"appendix.numeric_sequence_gap.{num}",
                message=(
                    f"В последовательности номеров приложений пропущен номер {num}."
                ),
                metadata={"missing_number": num},
                severity="recommendation",
            )
        )

    return out


def _issues_from_terminology_consistency(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("terminology_consistency_check"))
    raw = block.get("items")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = str(item.get("term_key") or "unknown").strip() or "unknown"
        variants = item.get("used_variants")
        var_list = variants if isinstance(variants, list) else []
        var_strs = [str(v).strip() for v in var_list if str(v).strip()]
        reason = str(item.get("reason") or "").strip()
        message = (
            reason
            if reason
            else (
                "Для одного термина в глоссарии использованы разные варианты наименования: "
                + ", ".join(var_strs)
                if var_strs
                else "Для одного термина использованы разные варианты наименования."
            )
        )
        snip = item.get("example_snippet")
        fragment = str(snip).strip() if snip is not None else None
        fragment_out = fragment if fragment else None
        meta = {
            k: item[k]
            for k in (
                "term_key",
                "canonical",
                "used_variants",
                "preferred_variant",
                "reason",
                "occurrence_count_by_variant",
            )
            if k in item
        }
        code = f"terminology.mixed_variants.{key}"
        out.append(
            make_issue(
                check_key="terminology_consistency_check",
                issue_code=code,
                message=message,
                fragment_text=fragment_out,
                metadata=meta,
                severity="recommendation",
            )
        )
    return out


def _issues_from_duplicate_formulations(checks: Mapping[str, Any]) -> list[Issue]:
    block = _as_mapping(checks.get("duplicate_formulations_check"))
    raw = block.get("items")
    if not isinstance(raw, list):
        return []
    out: list[Issue] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if kind == "exact_duplicate":
            text = str(item.get("text") or "").strip()
            message = reason if reason else "В документе повторяется одинаковая формулировка."
            idxs = item.get("fragment_indexes")
            locs: tuple[IssueLocation, ...] | None = None
            if isinstance(idxs, list):
                loc_tuples = tuple(
                    make_issue_location(fragment_index=i)
                    for i in idxs
                    if isinstance(i, int)
                )
                locs = loc_tuples if loc_tuples else None
            titles = item.get("section_titles")
            st_out = None
            if isinstance(titles, list) and titles:
                joined = ", ".join(str(t).strip() for t in titles if str(t).strip())
                st_out = joined if joined else None
            meta = {k: item[k] for k in ("kind", "occurrences", "fragment_indexes", "section_titles") if k in item}
            out.append(
                make_issue(
                    check_key="duplicate_formulations_check",
                    issue_code="duplicate.exact",
                    message=message,
                    fragment_text=text if text else None,
                    section_title=st_out,
                    metadata=meta,
                    severity="warning",
                    locations=locs,
                )
            )
        elif kind == "near_duplicate":
            ta = str(item.get("text_a") or "").strip()
            tb = str(item.get("text_b") or "").strip()
            message = reason if reason else "Обнаружены очень похожие формулировки."
            pair = " — ".join(p for p in (ta, tb) if p)
            meta = {k: item[k] for k in ("kind", "similarity", "text_a", "text_b", "reason") if k in item}
            out.append(
                make_issue(
                    check_key="duplicate_formulations_check",
                    issue_code="duplicate.near",
                    message=message,
                    fragment_text=pair if pair else None,
                    metadata=meta,
                    severity="warning",
                )
            )
    return out


# Adapters run in this order; :func:`build_document_issues` sorts the combined list.
_ADAPTERS: tuple[Callable[[Mapping[str, Any]], list[Issue]], ...] = (
    _issues_from_required_sections,
    _issues_from_section_order,
    _issues_from_presence_checks,
    _issues_from_numerical_characteristics,
    _issues_from_measurement_units,
    _issues_from_vague_wording,
    _issues_from_unverifiable_requirements,
    _issues_from_figure_references,
    _issues_from_table_references,
    _issues_from_appendix_references,
    _issues_from_terminology_consistency,
    _issues_from_duplicate_formulations,
)


def with_recommendation(issue: Issue) -> Issue:
    """Attach a mapped hint when absent; preserve an explicit ``recommendation``."""
    if issue.recommendation:
        return issue
    rec = recommendation_for_issue_code(issue.issue_code)
    if rec is None:
        return issue
    return replace(issue, recommendation=rec)


def build_document_issues(checks: Mapping[str, Any] | None) -> list[Issue]:
    """Return a deterministic flat list of issues for supported checks only."""
    if checks is None:
        return []
    base = _as_mapping(checks)
    collected: list[Issue] = []
    for adapter in _ADAPTERS:
        collected.extend(adapter(base))

    collected = [with_recommendation(i) for i in collected]

    def _sort_key(i: Issue) -> tuple[str, str, str, str]:
        frag = i.fragment_text or ""
        return (i.check_key, i.issue_code, i.message, frag)

    return sorted(collected, key=_sort_key)


def build_document_issues_serialized(checks: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """JSON-friendly list of issues (same order as :func:`build_document_issues`)."""
    return [issue_to_dict(i) for i in build_document_issues(checks)]
