"""Tests for Latin MVP review gates and curated-record readiness."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from multilang.services.latin_review import (
    LatinCuratedRecord,
    LatinReviewGate,
    LatinReviewGateName,
    LatinReviewStatus,
    assert_latin_records_export_ready,
    summarize_latin_review_records,
)


def _gate(status: str = "approved", *, reason: str | None = None) -> LatinReviewGate:
    return LatinReviewGate(status=status, reason=reason)


def _record(**overrides: object) -> LatinCuratedRecord:
    values: dict[str, object] = {
        "item_key": "latin-mvp-0001",
        "sequence": 1,
        "lemma": "et",
        "target_form": "et",
        "latin_sentence": "Et puer legit.",
        "source_pack_version": "latin-mvp-50-v1",
        "frequency_rank": 1,
        "frequency_source": "As mil palavras mais frequentes do latim (mylittlewordland)",
        "source_type": "reference_example",
        "citation": "Reference example composed from standard classroom Latin usage",
        "work_reference": "Multilang Latin MVP reference example set",
        "source_url_or_id": "multilang:latin-mvp:reference",
        "license_note": "Project-authored reference example; DCC lemma metadata attributed under CC BY-SA.",
        "replacement_reason": None,
        "uncertainty_reason": None,
        "source_gate": _gate(),
        "translation_gate": _gate(),
        "grammar_gate": _gate(),
        "audio_gate": _gate(),
    }
    values.update(overrides)
    return LatinCuratedRecord.model_validate(values)


def test_review_gate_accepts_blocking_status_with_reason() -> None:
    gate = LatinReviewGate(status="needs_review", reason="grammar ambiguous")

    assert gate.status == "needs_review"
    assert gate.reason == "grammar ambiguous"


def test_review_status_and_gate_names_are_exact() -> None:
    assert set(LatinReviewStatus.__args__) == {"needs_review", "approved", "rejected"}
    assert set(LatinReviewGateName.__args__) == {"source", "translation", "grammar", "audio"}


def test_blocking_gate_status_requires_non_blank_reason() -> None:
    with pytest.raises(ValidationError):
        LatinReviewGate(status="rejected")

    with pytest.raises(ValidationError):
        LatinReviewGate(status="needs_review", reason=" ")


def test_curated_record_requires_four_gates_and_preserves_provenance() -> None:
    record = _record(translation_gate=_gate("needs_review", reason="translation pending"))

    assert record.item_key == "latin-mvp-0001"
    assert record.frequency_rank == 1
    assert record.frequency_source == "As mil palavras mais frequentes do latim (mylittlewordland)"
    assert record.source_type == "reference_example"
    assert record.citation.startswith("Reference example")
    assert record.source_gate.status == "approved"
    assert record.translation_gate.status == "needs_review"

    payload = record.model_dump()
    del payload["audio_gate"]
    with pytest.raises(ValidationError):
        LatinCuratedRecord.model_validate(payload)


def test_summary_counts_only_all_approved_records_as_learner_ready() -> None:
    ready = _record()
    blocked = _record(
        item_key="latin-mvp-0002",
        sequence=2,
        frequency_rank=2,
        grammar_gate=_gate("needs_review", reason="grammar pending"),
    )

    summary = summarize_latin_review_records([ready, blocked])

    assert summary.total_records == 2
    assert summary.learner_ready_records == 1
    assert summary.blocked_records == 1
    assert summary.gate_counts["grammar"]["approved"] == 1
    assert summary.gate_counts["grammar"]["needs_review"] == 1
    assert summary.blocking_gates_by_item_key == {"latin-mvp-0002": ["grammar"]}


def test_export_ready_raises_scanner_readable_blockers() -> None:
    records = [
        _record(
            grammar_gate=_gate("needs_review", reason="grammar pending"),
            audio_gate=_gate("rejected", reason="audio failed"),
        )
    ]

    with pytest.raises(ValueError) as exc_info:
        assert_latin_records_export_ready(records)

    assert "latin_export_blocked item_key=latin-mvp-0001 gates=grammar,audio" in str(exc_info.value)


def test_export_ready_accepts_all_approved_records() -> None:
    assert_latin_records_export_ready([_record()])
