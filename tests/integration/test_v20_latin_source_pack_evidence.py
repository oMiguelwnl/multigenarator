"""FREQ/SRC/SENT Phase 23 scanner-readable Latin source-pack evidence."""

from __future__ import annotations

import json
from pathlib import Path

from multilang.domain.latin import LatinGenerationRequest
from multilang.domain.source_profiles import get_source_profile
from multilang.services.generate_job import GenerateJobService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.latin_source_pack import load_latin_mvp_source_pack, validate_latin_target_presence


PHASE_23_REQUIREMENTS = ("FREQ-01", "FREQ-02", "FREQ-03", "SRC-01", "SRC-02", "SENT-01", "SENT-02")


def test_freq_01_freq_02_frozen_50_entries_have_versioned_frequency_metadata() -> None:
    """FREQ-01/FREQ-02: frozen first-50 manifest exposes DCC rank/source metadata."""

    pack = load_latin_mvp_source_pack()

    assert PHASE_23_REQUIREMENTS == ("FREQ-01", "FREQ-02", "FREQ-03", "SRC-01", "SRC-02", "SENT-01", "SENT-02")
    assert pack.card_count == 50
    assert len(pack.entries) == 50
    assert pack.source_pack_version == "latin-mvp-50-v1"
    assert all(entry.frequency_rank >= 1 for entry in pack.entries)
    assert {entry.frequency_source for entry in pack.entries} == {"As mil palavras mais frequentes do latim (mylittlewordland)"}
    assert "CC BY-SA" in pack.frequency_attribution


def test_freq_03_sequence_preserves_frequency_ranks_with_didactic_rationales() -> None:
    """FREQ-03: sequence is didactic, but every row keeps rank and rationale evidence."""

    pack = load_latin_mvp_source_pack()
    service_result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert service_result.item_keys == [entry.item_key for entry in pack.entries]
    assert any(entry.sequence != entry.frequency_rank for entry in pack.entries)
    assert all(entry.inclusion_rationale for entry in pack.entries)
    assert all(entry.didactic_order_rationale for entry in pack.entries)
    assert "didactic sequence" in service_result.didactic_sequence_summary.casefold()


def test_src_01_src_02_license_provenance_and_source_type_are_auditable() -> None:
    """SRC-01/SRC-02: source provenance is license-gated and truthfully typed."""

    pack = load_latin_mvp_source_pack()
    source_types = {entry.source_type for entry in pack.entries}

    assert {entry.license_gate for entry in pack.entries} == {"approved"}
    assert source_types <= {"original_classical", "adapted_didactic", "reference_example"}
    assert "adapted_didactic" in source_types
    assert all(entry.citation and entry.work_reference and entry.source_url_or_id and entry.license_note for entry in pack.entries)
    assert all(not entry.original_citation_claim for entry in pack.entries if entry.source_type == "adapted_didactic")


def test_sent_01_sent_02_target_forms_validate_and_sequence_favors_clear_contexts() -> None:
    """SENT-01/SENT-02: displayed target forms are present and sentence sequence is explained."""

    pack = load_latin_mvp_source_pack()

    assert all(
        validate_latin_target_presence(entry.target_form, entry.latin_sentence, entry.target_match_mode)
        for entry in pack.entries
    )
    assert {entry.target_match_mode for entry in pack.entries} == {"exact"}
    assert all(
        "Rafael Falcon-style" in entry.didactic_order_rationale
        or "Didactic reorder" in entry.didactic_order_rationale
        or "Real-data reorder" in entry.didactic_order_rationale
        for entry in pack.entries
    )


def test_phase_23_asset_has_no_later_phase_payload_fields_or_large_scale_artifacts() -> None:
    """No-scope-creep: Phase 23 is source/frequency/sentence data only."""

    payload = json.loads(Path("data/latin_mvp/latin-mvp-50-v1.json").read_text(encoding="utf-8"))
    forbidden_fields = {
        "grammar",
        "short_translation_pt",
        "sentence_translation_pt",
        "word_audio",
        "sentence_audio",
        "apkg",
        "csv",
        "tsv",
    }

    assert payload["card_count"] == 50
    assert len(payload["entries"]) == 50
    assert all(forbidden_fields.isdisjoint(entry) for entry in payload["entries"])
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    assert "300-card" not in serialized
    assert "1000-card" not in serialized
    assert "3000-card" not in serialized
    assert "provider output" not in serialized


def test_existing_modes_import_with_latin_source_pack_loader_present() -> None:
    """Isolation: existing frequency, word-list, highlight, and phonetics-adjacent contracts remain importable."""

    assert get_source_profile("frequency").source_type == "frequency"
    assert get_source_profile("word-list").source_type == "word-list"
    assert get_source_profile("kindle-highlights").source_type == "kindle-highlights"
    assert get_source_profile("latin-mvp").source_type == "latin-mvp"
    assert GenerateJobService is not None
    assert IngestLexicalItemsService is not None
