"""Tests for Stage 12.2 — duplicate and near-duplicate formulations."""

from __future__ import annotations

from backend.app.checks.duplicate_formulations_check import check_document_duplicate_formulations


def _run(structure: dict, full_text: str) -> dict:
    return check_document_duplicate_formulations(structure, full_text)["duplicate_formulations_check"]


def test_empty_no_findings() -> None:
    out = _run({"sections": []}, "")
    assert out["has_findings"] is False
    assert out["item_count"] == 0
    assert out["items"] == []


def test_single_fragment_no_findings() -> None:
    s = "Система должна обрабатывать входящие запросы пользователей в штатном режиме."
    out = _run({"sections": []}, s)
    assert out["item_count"] == 0


def test_exact_duplicate_normalized_spacing_case_punctuation() -> None:
    a = "Система должна обеспечивать резервное копирование данных ежедневно."
    b = "  СИСТЕМА   ДОЛЖНА   обеспечивать  резервное копирование данных ежедневно! "
    out = _run({"sections": []}, f"{a} {b}")
    assert out["has_findings"] is True
    exact = [it for it in out["items"] if it["kind"] == "exact_duplicate"]
    assert len(exact) == 1
    assert exact[0]["occurrences"] == 2
    assert exact[0]["reason"]
    assert "fragment_indexes" in exact[0]


def test_exact_duplicate_three_occurrences_grouped() -> None:
    s = "Модуль должен журналировать все ошибки обработки входящих сообщений."
    out = _run({"sections": []}, f"{s} {s} {s}")
    exact = [it for it in out["items"] if it["kind"] == "exact_duplicate"]
    assert len(exact) == 1
    assert exact[0]["occurrences"] == 3


def test_near_duplicate_word_order() -> None:
    t1 = "Система должна быстро обрабатывать запросы пользователей в пиковой нагрузке."
    t2 = "Система должна обрабатывать запросы пользователей быстро в пиковой нагрузке."
    out = _run({"sections": []}, f"{t1} {t2}")
    near = [it for it in out["items"] if it["kind"] == "near_duplicate"]
    assert len(near) >= 1
    n0 = near[0]
    assert n0["similarity"] >= 0.88
    assert n0["text_a"] and n0["text_b"]
    assert set([n0["text_a"], n0["text_b"]]) == {t1, t2}
    assert n0["reason"]


def test_near_duplicate_auth_phrasing() -> None:
    t1 = "Пользователь должен пройти аутентификацию перед входом в защищённую зону."
    t2 = "Перед входом в защищённую зону пользователь должен пройти аутентификацию."
    out = _run({"sections": []}, f"{t1} {t2}")
    near = [it for it in out["items"] if it["kind"] == "near_duplicate"]
    assert len(near) >= 1


def test_unrelated_sentences_not_near() -> None:
    t1 = "Система должна хранить журнал аудита не менее двенадцати месяцев подряд."
    t2 = "Интерфейс должен отображать уведомления об ошибках в понятном для оператора виде."
    out = _run({"sections": []}, f"{t1} {t2}")
    assert out["item_count"] == 0


def test_cross_section_exact_duplicate_metadata() -> None:
    s = "Сервис должен проверять целостность данных при каждом сохранении на диск."
    structure = {
        "sections": [
            {"title": "3. Требования", "content_text": s},
            {"title": "5. Надёжность", "content_text": s},
        ]
    }
    out = _run(structure, "")
    exact = [it for it in out["items"] if it["kind"] == "exact_duplicate"]
    assert len(exact) == 1
    titles = set(exact[0].get("section_titles", []))
    assert titles == {"3. Требования", "5. Надёжность"}


def test_numbered_heading_stub_skipped() -> None:
    structure = {
        "sections": [
            {"title": "Раздел", "content_text": "2.3 Общие положения"},
        ]
    }
    out = _run(structure, "")
    assert out["item_count"] == 0
