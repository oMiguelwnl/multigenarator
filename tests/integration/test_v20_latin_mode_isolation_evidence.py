"""MODE-01/MODE-02/MODE-03 Phase 22 Latin mode isolation evidence."""

from __future__ import annotations

from multilang.domain.audio import AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    export_field_names_for_source_type,
)
from multilang.domain.latin import LatinGenerationRequest, LatinVariant
from multilang.domain.source_profiles import get_source_profile
from multilang.services.audio_synthesis import AudioSynthesisService
from multilang.services.audio_voice_registry import VOICE_REGISTRY_VERSION, get_voice_registry
from multilang.services.latin_mvp import LatinMvpGenerationService
from multilang.services.russian_phoneme_deck import PHONEME_FIELD_NAMES
from multilang.services.text_review import ReviewReport, ReviewReportItem, TextReviewService


PHASE_22_REQUIREMENTS = ("MODE-01", "MODE-02", "MODE-03")

V20_NORMAL_FIELD_NAMES = (
    "SortIndex",
    "word",
    "IPA",
    "Definitions",
    "Example Sentence",
    "Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)


def test_mode_01_mode_02_latin_mvp_service_reports_classical_50_card_contract() -> None:
    """MODE-01/MODE-02: Latin path uses latin-mvp metadata, not frequency metadata."""

    result = LatinMvpGenerationService().start(LatinGenerationRequest())

    assert PHASE_22_REQUIREMENTS == ("MODE-01", "MODE-02", "MODE-03")
    assert result.metadata.language_code == "la"
    assert result.metadata.variant is LatinVariant.CLASSICAL
    assert result.metadata.source_pack_version == "latin-mvp-50-v1"
    assert result.metadata.card_count == 50
    assert result.source_type == "latin-mvp"
    assert result.item_keys[0] == "latin-mvp-0001"
    assert result.item_keys[-1] == "latin-mvp-0050"


def test_mode_01_mode_03_latin_mvp_source_profile_is_distinct_from_existing_modes() -> None:
    """MODE-01/MODE-03: Latin profile remains isolated from shipped source profiles."""

    latin_profile = get_source_profile("latin-mvp")
    existing_profiles = (
        get_source_profile("frequency"),
        get_source_profile("word-list"),
        get_source_profile("kindle-highlights"),
    )

    assert latin_profile.source_type == "latin-mvp"
    assert latin_profile.note_type_name == "Multilang::Latin MVP Card"
    assert latin_profile.template_name == "latin_mvp_card"
    assert latin_profile not in existing_profiles


def test_mode_03_existing_export_field_contracts_remain_unchanged() -> None:
    """MODE-03: Latin profile does not mutate normal/manual/highlight export fields."""

    assert FREQUENCY_EXPORT_CARD_FIELD_NAMES == V20_NORMAL_FIELD_NAMES
    assert export_field_names_for_source_type("frequency") == V20_NORMAL_FIELD_NAMES
    assert "Translation" in export_field_names_for_source_type("frequency")
    assert "word_audio" in export_field_names_for_source_type("frequency")
    assert "sentence_audio" in export_field_names_for_source_type("frequency")
    assert "Image" in export_field_names_for_source_type("frequency")

    assert export_field_names_for_source_type("word-list") == MANUAL_EXPORT_CARD_FIELD_NAMES
    assert export_field_names_for_source_type("kindle-highlights") == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert "Translation" not in export_field_names_for_source_type("word-list")
    assert "word_audio" not in export_field_names_for_source_type("kindle-highlights")


def test_mode_03_existing_phonetics_contract_remains_disjoint_from_learner_fields() -> None:
    """MODE-03: Latin profile does not mutate the Russian/Polish phoneme field contract."""

    forbidden_learner_fields = {"word", "Word", "IPA", "Definitions", "Definition", "Translation", "Image"}

    assert "word_audio" in PHONEME_FIELD_NAMES
    assert "sentence_audio" in PHONEME_FIELD_NAMES
    assert set(PHONEME_FIELD_NAMES).isdisjoint(forbidden_learner_fields)
    assert set(PHONEME_FIELD_NAMES) != set(FREQUENCY_EXPORT_CARD_FIELD_NAMES)
    assert set(PHONEME_FIELD_NAMES) != set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)


def test_mode_03_review_and_audio_symbols_import_offline_with_latin_contracts_present() -> None:
    """MODE-03: review/audio boundaries remain importable without live providers or credentials."""

    assert TextReviewService is not None
    assert ReviewReport is not None
    assert ReviewReportItem is not None
    assert AudioSynthesisService is not None
    assert AudioAssetRecord is not None
    assert AudioSynthesisStatus.SYNTHESIZED.value == "synthesized"
    assert VOICE_REGISTRY_VERSION
    assert get_voice_registry()
