"""Integration tests for the committed Latin MVP curation asset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from multilang.services.latin_review import (
    LatinCuratedRecord,
    assert_latin_records_export_ready,
    load_latin_curated_records,
)
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


def test_load_latin_curated_records_returns_50_models() -> None:
    records = load_latin_curated_records()

    assert len(records) == 50
    assert all(isinstance(record, LatinCuratedRecord) for record in records)
    assert records[0].item_key == "latin-mvp-0001"
    assert records[-1].item_key == "latin-mvp-0050"


def test_loader_rejects_malformed_json_or_invalid_review_state(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="curation JSON is malformed"):
        load_latin_curated_records(malformed)

    source_pack = load_latin_mvp_source_pack()
    invalid_payload = [_curation_record_from_entry(entry) for entry in source_pack.entries]
    invalid_payload[0]["translation_gate"] = {"status": "pending", "reason": "bad status"}
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(invalid_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="failed validation"):
        load_latin_curated_records(invalid)


def test_curation_records_match_source_pack_identity_order_and_provenance() -> None:
    records = load_latin_curated_records()
    source_pack = load_latin_mvp_source_pack()

    assert [record.item_key for record in records] == [entry.item_key for entry in source_pack.entries]
    assert [record.sequence for record in records] == [entry.sequence for entry in source_pack.entries]
    for record, entry in zip(records, source_pack.entries, strict=True):
        assert record.source_pack_version == entry.source_pack_version
        assert record.lemma == entry.lemma
        assert record.target_form == entry.target_form
        assert record.latin_sentence == entry.latin_sentence
        assert record.frequency_rank == entry.frequency_rank
        assert record.frequency_source == entry.frequency_source
        assert record.source_type == entry.source_type
        assert record.citation == entry.citation
        assert record.work_reference == entry.work_reference
        assert record.source_url_or_id == entry.source_url_or_id
        assert record.license_note == entry.license_note


def test_curation_asset_exposes_four_gates_and_blocks_export_until_later_phases() -> None:
    records = load_latin_curated_records()

    assert {record.source_gate.status for record in records} == {"approved"}
    assert {record.grammar_gate.status for record in records} == {"approved"}
    assert {record.translation_gate.status for record in records} == {"needs_review"}
    assert {record.audio_gate.status for record in records} == {"needs_review"}
    assert {record.translation_gate.reason for record in records} == {"translation_pending_phase_26"}
    assert {record.audio_gate.reason for record in records} == {"audio_pending_phase_27"}
    with pytest.raises(ValueError, match="latin_export_blocked"):
        assert_latin_records_export_ready(records)


def test_loader_rejects_source_pack_provenance_drift(tmp_path: Path) -> None:
    source_pack = load_latin_mvp_source_pack()
    payload = [_curation_record_from_entry(entry) for entry in source_pack.entries]
    payload[0]["frequency_rank"] = 999
    path = tmp_path / "drift.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="provenance mismatch"):
        load_latin_curated_records(path)


def _curation_record_from_entry(entry: object) -> dict[str, object]:
    return {
        "item_key": entry.item_key,
        "sequence": entry.sequence,
        "lemma": entry.lemma,
        "target_form": entry.target_form,
        "latin_sentence": entry.latin_sentence,
        "source_pack_version": entry.source_pack_version,
        "frequency_rank": entry.frequency_rank,
        "frequency_source": entry.frequency_source,
        "source_type": entry.source_type,
        "citation": entry.citation,
        "work_reference": entry.work_reference,
        "source_url_or_id": entry.source_url_or_id,
        "license_note": entry.license_note,
        "replacement_reason": None,
        "uncertainty_reason": None,
        "source_gate": {"status": "approved"},
        "translation_gate": {"status": "needs_review", "reason": "translation_pending_phase_26"},
        "grammar_gate": {"status": "approved"},
        "audio_gate": {"status": "needs_review", "reason": "audio_pending_phase_27"},
    }
