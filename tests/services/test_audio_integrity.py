"""Tests for strict word-audio integrity checks."""

from __future__ import annotations

import pytest

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.services.audio_integrity import AudioIntegrityError, assert_word_audio_matches_word, word_audio_matches_word


def make_record(
    *,
    word: str = "coração",
    normalized_display: str | None = None,
    tts_text: str | None = None,
    provenance_text_hash: str | None = None,
    asset_kind: AudioAssetKind = AudioAssetKind.WORD,
) -> AudioAssetRecord:
    normalized = NormalizedTtsInput(
        display_text=normalized_display or word,
        tts_text=tts_text or word,
        ssml_text=f'<speak version="1.0">{tts_text or word}</speak>',
    )
    return AudioAssetRecord(
        job_id="job-123",
        item_key="item-1",
        asset_kind=asset_kind,
        display_text=normalized.display_text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="pt-BR-FranciscaNeural",
            locale="pt-BR",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=provenance_text_hash or normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path="audio/word/hash.mp3",
            byte_size=4096,
            duration_ms=1200,
            status=AudioSynthesisStatus.SYNTHESIZED,
        ),
    )


def assert_integrity_error(asset: AudioAssetRecord, word: str, field_name: str) -> None:
    with pytest.raises(AudioIntegrityError) as exc_info:
        assert_word_audio_matches_word(asset, word, item_key="item-1")

    message = str(exc_info.value)
    assert "word_audio" in message
    assert "Word" in message
    assert "item-1" in message
    assert field_name in message
    assert "C:\\" not in message


def test_word_asset_matches_when_all_word_metadata_matches_exactly() -> None:
    asset = make_record(word="coração")

    assert_word_audio_matches_word(asset, "  coração  ", item_key="item-1")

    assert word_audio_matches_word(asset, "coração") is True


@pytest.mark.parametrize(
    ("asset", "field_name"),
    [
        (make_record(word="casa"), "display_text"),
        (make_record(word="coração", normalized_display="coração", tts_text="coracao"), "normalized_input.tts_text"),
        (make_record(word="coração", provenance_text_hash="stale-hash"), "provenance.text_hash"),
    ],
)
def test_word_asset_fails_with_item_specific_metadata_diagnostics(asset: AudioAssetRecord, field_name: str) -> None:
    assert_integrity_error(asset, "coração", field_name)

    assert word_audio_matches_word(asset, "coração") is False


def test_empty_expected_word_fails_deterministically() -> None:
    assert_integrity_error(make_record(word="coração"), "   ", "Word")


def test_accent_stripped_tts_text_does_not_match_accented_word() -> None:
    asset = make_record(word="ação", tts_text="acao")

    assert_integrity_error(asset, "ação", "normalized_input.tts_text")


def test_sentence_asset_is_never_treated_as_matching_word_audio() -> None:
    asset = make_record(word="Eu uso ação todos os dias.", asset_kind=AudioAssetKind.SENTENCE)

    assert_integrity_error(asset, "ação", "asset_kind")
