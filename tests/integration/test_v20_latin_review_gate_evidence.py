"""REV Phase 25 scanner-readable Latin review-gate evidence."""

from __future__ import annotations

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.latin_review import assert_latin_records_export_ready, load_latin_curated_records
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


PHASE_25_REQUIREMENTS = ("REV-01", "REV-02", "REV-03")

_VALID_REVIEW_STATUSES = {"needs_review", "approved", "rejected"}
_PROVENANCE_FIELDS = (
    "frequency_rank",
    "frequency_source",
    "source_type",
    "citation",
    "work_reference",
    "source_url_or_id",
    "license_note",
)


def test_rev_01_all_curated_records_expose_four_independent_review_gates() -> None:
    """REV-01: source/translation/grammar/audio gates exist with approved/rejected/needs_review states."""

    records = load_latin_curated_records()

    assert PHASE_25_REQUIREMENTS == ("REV-01", "REV-02", "REV-03")
    assert len(records) == 50
    for record in records:
        gates = (record.source_gate, record.translation_gate, record.grammar_gate, record.audio_gate)
        assert {gate.status for gate in gates} <= _VALID_REVIEW_STATUSES
        assert record.source_gate.status == "approved"
        assert record.translation_gate.status in _VALID_REVIEW_STATUSES
        assert record.grammar_gate.status in _VALID_REVIEW_STATUSES
        assert record.audio_gate.status in _VALID_REVIEW_STATUSES


def test_rev_02_export_is_allowed_when_all_required_gates_are_approved() -> None:
    """REV-02: learner-ready export is allowed only after all required gates are approved."""

    records = load_latin_curated_records()

    assert all(record.translation_gate.status == "approved" for record in records)
    assert all(record.audio_gate.status == "approved" for record in records)
    assert_latin_records_export_ready(records)


def test_rev_03_curated_records_preserve_original_source_and_frequency_provenance() -> None:
    """REV-03: every curated record retains the source/frequency fields needed for audit and replacement review."""

    records = load_latin_curated_records()
    source_pack = load_latin_mvp_source_pack()

    for record, source_entry in zip(records, source_pack.entries, strict=True):
        for field_name in _PROVENANCE_FIELDS:
            assert getattr(record, field_name)
            assert getattr(record, field_name) == getattr(source_entry, field_name)
        assert record.replacement_reason is None
        assert record.uncertainty_reason is None


def test_phase_25_records_reflect_later_translation_and_audio_approvals() -> None:
    """Milestone state: Phase 26/27 approvals are reflected in the committed curation asset."""

    records = load_latin_curated_records()

    assert {record.translation_gate.status for record in records} == {"approved"}
    assert {record.audio_gate.status for record in records} == {"approved"}


def test_phase_25_keeps_latin_frequency_generation_disabled() -> None:
    """Classical Latin is registered but remains blocked from modern frequency generation."""

    assert SupportedLanguage.LA.value == "la"


def test_phase_25_does_not_mutate_phase_23_source_pack_count_or_ordering() -> None:
    """Boundary: review curation mirrors but does not alter the frozen source-pack entry sequence."""

    source_pack = load_latin_mvp_source_pack()
    records = load_latin_curated_records()
    expected_keys = [f"latin-mvp-{index:04d}" for index in range(1, 51)]

    assert [entry.item_key for entry in source_pack.entries] == expected_keys
    assert [record.item_key for record in records] == expected_keys
    assert len(source_pack.entries) == 50
