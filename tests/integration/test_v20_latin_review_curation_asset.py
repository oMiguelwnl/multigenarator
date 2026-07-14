"""Integration tests for the committed Latin MVP curation asset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from multilang.services.latin_review import (
    DEFAULT_LATIN_MVP_CURATION_PATH,
    assert_latin_records_export_ready,
    load_latin_curated_records,
    summarize_latin_review_records,
)
from multilang.services.latin_source_pack import load_latin_mvp_source_pack


def test_load_latin_curated_records_returns_50_models_from_default_asset() -> None:
    records = load_latin_curated_records()

    assert len(records) == 50
    assert records[0].item_key == "latin-mvp-0001"
    assert records[-1].item_key == "latin-mvp-0050"
    assert all(record.source_gate.status == "approved" for record in records)
    assert all(record.grammar_gate.status == "approved" for record in records)
    assert all(record.translation_gate.status == "approved" for record in records)
    assert all(record.audio_gate.status == "approved" for record in records)


def test_loader_rejects_malformed_json_and_invalid_review_states(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        load_latin_curated_records(malformed)

    payload = json.loads(DEFAULT_LATIN_MVP_CURATION_PATH.read_text(encoding="utf-8"))
    payload[0]["translation_gate"]["status"] = "done"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="failed validation"):
        load_latin_curated_records(invalid)


def test_curation_records_match_source_pack_identity_and_provenance() -> None:
    records = load_latin_curated_records()
    source_pack = load_latin_mvp_source_pack()

    for record, source_entry in zip(records, source_pack.entries, strict=True):
        assert record.item_key == source_entry.item_key
        assert record.sequence == source_entry.sequence
        assert record.source_pack_version == source_entry.source_pack_version
        assert record.lemma == source_entry.lemma
        assert record.target_form == source_entry.target_form
        assert record.frequency_rank == source_entry.frequency_rank
        assert record.frequency_source == source_entry.frequency_source
        assert record.source_type == source_entry.source_type
        assert record.citation == source_entry.citation
        assert record.license_note == source_entry.license_note


def test_loader_fails_on_source_pack_provenance_drift(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_LATIN_MVP_CURATION_PATH.read_text(encoding="utf-8"))
    payload[0]["frequency_rank"] = 999
    drifted = tmp_path / "drifted.json"
    drifted.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="provenance mismatch"):
        load_latin_curated_records(drifted)


def test_curation_asset_is_export_ready_after_later_gates_are_approved() -> None:
    records = load_latin_curated_records()
    summary = summarize_latin_review_records(records)

    assert summary.total_records == 50
    assert summary.learner_ready_records == 50
    assert summary.blocked_records == 0
    assert summary.gate_counts["source"]["approved"] == 50
    assert summary.gate_counts["translation"]["approved"] == 50
    assert summary.gate_counts["grammar"]["approved"] == 50
    assert summary.gate_counts["audio"]["approved"] == 50
    assert_latin_records_export_ready(records)
