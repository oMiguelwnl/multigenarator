"""REV-01/REV-02/REV-03 Phase 25 scanner-readable Latin review evidence."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.services.latin_review import assert_latin_records_export_ready, load_latin_curated_records
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


PHASE_25_REQUIREMENTS = ("REV-01", "REV-02", "REV-03")
VALID_REVIEW_STATUSES = {"needs_review", "approved", "rejected"}


def test_rev_01_all_curated_records_expose_four_independent_review_gates() -> None:
    """REV-01: source/translation/grammar/audio gate states are explicit on every record."""

    records = load_latin_curated_records()

    assert PHASE_25_REQUIREMENTS == ("REV-01", "REV-02", "REV-03")
    assert len(records) == 50
    for record in records:
        gates = (record.source_gate, record.translation_gate, record.grammar_gate, record.audio_gate)
        assert {gate.status for gate in gates} <= VALID_REVIEW_STATUSES
        assert record.source_gate.status == "approved"
        assert record.grammar_gate.status == "approved"
        assert record.translation_gate.status == "needs_review"
        assert record.audio_gate.status == "needs_review"


def test_rev_02_export_readiness_fails_closed_until_all_gates_are_approved() -> None:
    """REV-02: learner-ready export is blocked by any non-approved required gate."""

    records = load_latin_curated_records()

    try:
        assert_latin_records_export_ready(records)
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover - this is a fail-closed evidence assertion.
        raise AssertionError("Latin review records unexpectedly passed export readiness")

    assert "latin_export_blocked item_key=latin-mvp-0001 gates=translation,audio" in message
    assert "latin_export_blocked item_key=latin-mvp-0050 gates=translation,audio" in message


def test_rev_03_curated_records_preserve_source_and_frequency_provenance() -> None:
    """REV-03: replacement/uncertainty review state does not remove source provenance."""

    records = load_latin_curated_records()

    for record in records:
        assert record.frequency_rank >= 1
        assert record.frequency_source == "DCC Latin Core Vocabulary"
        assert record.source_type in {"original_classical", "adapted_didactic", "reference_example"}
        assert record.citation
        assert record.work_reference
        assert record.source_url_or_id
        assert record.license_note
        assert hasattr(record, "replacement_reason")
        assert hasattr(record, "uncertainty_reason")


def test_phase_25_does_not_prematurely_approve_translation_or_audio_scope() -> None:
    """No-scope-creep: Phase 26 translation and Phase 27 audio remain pending."""

    records = load_latin_curated_records()

    assert {record.translation_gate.status for record in records} == {"needs_review"}
    assert {record.audio_gate.status for record in records} == {"needs_review"}
    assert {record.translation_gate.reason for record in records} == {"translation_pending_phase_26"}
    assert {record.audio_gate.reason for record in records} == {"audio_pending_phase_27"}


def test_phase_25_keeps_latin_outside_modern_supported_languages() -> None:
    """No-scope-creep: Classical Latin review records do not alter modern generation languages."""

    assert "la" not in {language.value for language in SupportedLanguage}


def test_phase_25_does_not_mutate_phase_23_source_pack_count_or_ordering() -> None:
    """No-scope-creep: review curation stays keyed to the frozen source-pack order."""

    records = load_latin_curated_records()
    source_pack = load_latin_mvp_source_pack()

    assert len(source_pack.entries) == 50
    assert [entry.item_key for entry in source_pack.entries] == [f"latin-mvp-{index:04d}" for index in range(1, 51)]
    assert [record.item_key for record in records] == [entry.item_key for entry in source_pack.entries]
