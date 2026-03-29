"""Tests for Stage 10.1 vague wording dictionary scan."""

from __future__ import annotations

from backend.app.checks.vague_wording_check import check_document_vague_wording


def _vw(structure: dict, full_text: str) -> dict:
    return check_document_vague_wording(structure, full_text)["vague_wording_check"]


def test_empty_full_text() -> None:
    out = _vw({"sections": []}, "")
    assert out["has_findings"] is False
    assert out["findings"] == []
    assert out["finding_count"] == 0


def test_whitespace_only() -> None:
    out = _vw({"sections": []}, "  \n\t  ")
    assert out["has_findings"] is False
    assert out["finding_count"] == 0


def test_no_signals() -> None:
    out = _vw({"sections": []}, "Система обрабатывает запросы в соответствии с регламентом.")
    assert out["has_findings"] is False
    assert out["findings"] == []


def test_single_dictionary_match_excerpt_and_metadata() -> None:
    text = "Система должна быстро обрабатывать запросы пользователя."
    out = _vw({"sections": []}, text)
    assert out["has_findings"] is True
    assert out["finding_count"] == 1
    f0 = out["findings"][0]
    assert f0["phrase"] == "быстро"
    assert f0["match_type"] == "dictionary_phrase"
    assert f0["source_kind"] == "full_text"
    assert f0["category"] == "speed"
    assert f0["description"]
    assert "быстро" in f0["text_excerpt"]


def test_casefolding() -> None:
    out = _vw({"sections": []}, "Требование: БЫСТРО реагировать на события.")
    assert out["finding_count"] == 1
    assert out["findings"][0]["phrase"] == "быстро"


def test_multiline_whitespace_normalized_like_other_checks() -> None:
    text = "Модуль\nдолжен   эффективно\nиспользовать ресурсы."
    out = _vw({"sections": []}, text)
    assert out["finding_count"] == 1
    assert out["findings"][0]["phrase"] == "эффективно"


def test_repeated_phrase_two_findings() -> None:
    text = "Сервис работает быстро. Пользователь ожидает быстро ответ."
    out = _vw({"sections": []}, text)
    assert out["finding_count"] == 2
    assert all(x["phrase"] == "быстро" for x in out["findings"])


def test_substring_not_word_match() -> None:
    """«возможность» as substring inside a longer token must not match."""
    out = _vw({"sections": []}, "невозможность отказа исключена.")
    assert out["has_findings"] is False


def test_longer_phrase_wins_over_embedded_shorter() -> None:
    text = "Модуль должен обеспечивать возможность масштабирования."
    out = _vw({"sections": []}, text)
    phrases = {f["phrase"] for f in out["findings"]}
    assert "должен обеспечивать возможность" in phrases
    assert "возможность" not in phrases
