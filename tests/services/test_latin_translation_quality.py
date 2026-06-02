"""Tests for deterministic Portuguese QA of Latin MVP translations."""

from __future__ import annotations

from dataclasses import replace

from pydantic import ValidationError

import pytest

from multilang.services.latin_source_pack import load_latin_mvp_source_pack
from multilang.services.latin_translation_quality import (
    LatinPortugueseTranslationEntry,
    LatinPortugueseTranslationPack,
    LatinPortugueseTranslationQaService,
    LatinPortugueseTranslationQaStatus,
)


def _entry(**overrides: object) -> LatinPortugueseTranslationEntry:
    values = {
        "item_key": "latin-mvp-0001",
        "source_pack_version": "latin-mvp-50-v1",
        "lemma": "et",
        "target_form": "et",
        "latin_sentence": "Et puer legit.",
        "short_translation_pt": "e",
        "sentence_translation_pt": "E o menino lê.",
        "translation_notes": "Contexto simples com conjunção inicial.",
        "review_status": "needs_review",
    }
    values.update(overrides)
    return LatinPortugueseTranslationEntry.model_validate(values)


def test_valid_short_and_sentence_translation_pass() -> None:
    entry = _entry(lemma="puer", target_form="puer", short_translation_pt="menino")

    result = LatinPortugueseTranslationQaService().validate_entry(entry)

    assert result.status is LatinPortugueseTranslationQaStatus.PASSED
    assert result.issues == []


@pytest.mark.parametrize(
    ("field", "value", "issue_code"),
    [
        ("short_translation_pt", " ", "blank_field"),
        ("sentence_translation_pt", "The boy reads.", "english_leakage"),
        ("short_translation_pt", "boy", "english_leakage"),
        ("sentence_translation_pt", "Et puer legit.", "latin_copy"),
        ("sentence_translation_pt", "menino", "dictionary_only_sentence"),
    ],
)
def test_invalid_translation_text_fails_with_explicit_issue_codes(field: str, value: str, issue_code: str) -> None:
    data = _entry().model_dump()
    data[field] = value
    if value.strip():
        entry = LatinPortugueseTranslationEntry.model_validate(data)
        result = LatinPortugueseTranslationQaService().validate_entry(entry)
    else:
        with pytest.raises(ValidationError) as exc_info:
            LatinPortugueseTranslationEntry.model_validate(data)
        assert "must not be blank" in str(exc_info.value)
        return

    assert result.status is LatinPortugueseTranslationQaStatus.FAILED
    assert issue_code in {issue.code for issue in result.issues}


def test_translation_pack_must_match_source_pack_order_and_context() -> None:
    source_pack = load_latin_mvp_source_pack()
    translations = LatinPortugueseTranslationPack.model_validate(
        {
            "source_pack_version": source_pack.source_pack_version,
            "translation_pack_version": "latin-mvp-50-pt-test",
            "entries": [
                {
                    "item_key": source.item_key,
                    "source_pack_version": source.source_pack_version,
                    "lemma": source.lemma,
                    "target_form": source.target_form,
                    "latin_sentence": source.latin_sentence,
                    "short_translation_pt": "teste",
                    "sentence_translation_pt": f"Tradução portuguesa para {source.item_key}.",
                    "translation_notes": "Entrada sintética apenas para teste de alinhamento.",
                    "review_status": "needs_review",
                }
                for source in source_pack.entries
            ],
        }
    )

    result = LatinPortugueseTranslationQaService().validate_pack(translations, source_pack)

    assert result.status is LatinPortugueseTranslationQaStatus.PASSED
    assert result.qa_summary()["entry_count"] == 50


@pytest.mark.parametrize(
    ("field", "value", "issue_code"),
    [
        ("source_pack_version", "other", "source_pack_version_mismatch"),
        ("lemma", "alius", "lemma_mismatch"),
        ("target_form", "alius", "target_form_mismatch"),
        ("latin_sentence", "Alius legit.", "latin_sentence_mismatch"),
    ],
)
def test_source_pack_drift_fails_pack_validation(field: str, value: str, issue_code: str) -> None:
    source_pack = load_latin_mvp_source_pack()
    first = source_pack.entries[0]
    pack = LatinPortugueseTranslationPack.model_validate(
        {
            "source_pack_version": source_pack.source_pack_version,
            "translation_pack_version": "latin-mvp-50-pt-test",
            "entries": [
                {
                    "item_key": first.item_key,
                    "source_pack_version": first.source_pack_version,
                    "lemma": first.lemma,
                    "target_form": first.target_form,
                    "latin_sentence": first.latin_sentence,
                    "short_translation_pt": "e",
                    "sentence_translation_pt": "E o menino lê.",
                    "translation_notes": "Entrada sintética.",
                    "review_status": "needs_review",
                    field: value,
                }
            ],
        }
    )

    result = LatinPortugueseTranslationQaService().validate_pack(pack, source_pack)

    assert result.status is LatinPortugueseTranslationQaStatus.FAILED
    assert issue_code in {issue.code for issue in result.issues}


def test_qa_summary_reports_issue_and_review_status_counts() -> None:
    result = LatinPortugueseTranslationQaService().validate_entry(_entry(sentence_translation_pt="boy"))

    summary = result.qa_summary()

    assert summary["entry_count"] == 1
    assert summary["passed_count"] == 0
    assert summary["failed_count"] == 1
    assert summary["issue_counts"]["english_leakage"] == 1
    assert summary["review_status_counts"] == {"needs_review": 1, "approved": 0, "rejected": 0}
