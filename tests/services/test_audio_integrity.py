"""Tests for strict word-audio integrity checks."""

from __future__ import annotations

from hashlib import sha256

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
from multilang.services.audio_integrity import (
    AudioIntegrityError,
    assert_word_audio_matches_word,
    word_audio_matches_word,
)


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


def test_normalized_display_text_must_match_expected_word_exactly() -> None:
    normalized = NormalizedTtsInput(display_text="acao", tts_text="ação")
    asset = AudioAssetRecord.model_construct(
        job_id="job-123",
        item_key="item-1",
        asset_kind=AudioAssetKind.WORD,
        display_text="ação",
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="pt-BR-FranciscaNeural",
            locale="pt-BR",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path="audio/word/hash.mp3",
            byte_size=4096,
            duration_ms=1200,
            status=AudioSynthesisStatus.SYNTHESIZED,
        ),
    )

    assert_integrity_error(asset, "ação", "normalized_input.display_text")


def test_sentence_asset_is_never_treated_as_matching_word_audio() -> None:
    asset = make_record(word="Eu uso ação todos os dias.", asset_kind=AudioAssetKind.SENTENCE)

    assert_integrity_error(asset, "ação", "asset_kind")


@pytest.mark.parametrize(("display", "tts"), [("l’homme", "l'homme"), ("cafe\u0301", "café"), ("très  bien", "très bien")])
def test_synthesis_normalization_keeps_display_text_and_accents(display: str, tts: str) -> None:
    from multilang.services.audio_integrity import normalize_tts_text

    asset = make_record(word=display, tts_text=tts)

    assert normalize_tts_text(display) == tts
    assert_word_audio_matches_word(asset, display)
    assert asset.display_text == display


def test_stale_normalized_text_hash_is_rejected() -> None:
    asset = make_record(word="coração")
    asset.normalized_input.text_hash = "stale-hash"

    assert_integrity_error(asset, "coração", "normalized_input.text_hash")


def test_sentence_integrity_uses_normalized_speech_and_checks_hashes() -> None:
    from multilang.services.audio_integrity import assert_sentence_audio_matches_sentence

    sentence = "L’homme lit chaque soir."
    asset = make_record(word=sentence, tts_text="L'homme lit chaque soir.", asset_kind=AudioAssetKind.SENTENCE)
    assert_sentence_audio_matches_sentence(asset, sentence)
    asset.provenance.text_hash = "stale-hash"

    with pytest.raises(AudioIntegrityError, match="sentence_audio.*item-1.*provenance.text_hash"):
        assert_sentence_audio_matches_sentence(asset, sentence)


@pytest.mark.parametrize("field", ["normalized_input", "provenance"])
def test_changed_ssml_hash_is_rejected(field: str) -> None:
    asset = make_record(word="coração")
    getattr(asset, field).ssml_hash = "stale-hash"

    assert_integrity_error(asset, "coração", f"{field}.ssml_hash")


def replace_ssml(asset: AudioAssetRecord, ssml: str) -> AudioAssetRecord:
    asset.normalized_input.ssml_text = ssml
    digest = sha256(ssml.encode("utf-8")).hexdigest()
    asset.normalized_input.ssml_hash = digest
    asset.provenance.ssml_hash = digest
    return asset


@pytest.mark.parametrize("asset_kind", [AudioAssetKind.WORD, AudioAssetKind.SENTENCE])
def test_self_consistent_ssml_for_different_words_is_rejected(asset_kind: AudioAssetKind) -> None:
    from multilang.services.audio_integrity import assert_sentence_audio_matches_sentence

    text = "coração" if asset_kind is AudioAssetKind.WORD else "Eu cuido do coração."
    asset = replace_ssml(make_record(word=text, asset_kind=asset_kind), "<speak>outro texto</speak>")
    check = assert_word_audio_matches_word if asset_kind is AudioAssetKind.WORD else assert_sentence_audio_matches_sentence

    with pytest.raises(AudioIntegrityError, match="ssml.*spoken"):
        check(asset, text)


@pytest.mark.parametrize("ssml", [
    '<speak><audio src="https://example.invalid/speech.mp3">coração</audio></speak>',
    '<speak><sub alias="outro">coração</sub></speak>',
    '<speak><lexicon uri="https://example.invalid/lexicon"/>coração</speak>',
    '<!DOCTYPE speak [<!ENTITY word "coração">]><speak>&word;</speak>',
    '<speak xmlns="urn:unapproved">coração</speak>',
    '<speak><prosody onload="active">coração</prosody></speak>',
    '<speak>coração',
    '<speak>' + ('<prosody>' * 257) + 'coração' + ('</prosody>' * 257) + '</speak>',
])
def test_unsupported_ssml_is_rejected_even_with_matching_hashes(ssml: str) -> None:
    asset = replace_ssml(make_record(), ssml)

    with pytest.raises(AudioIntegrityError, match="ssml"):
        assert_word_audio_matches_word(asset, "coração")


@pytest.mark.parametrize("ssml", [
    "coração",
    '<speak version="1.0"><prosody rate="-10%">coração</prosody></speak>',
    '<speak xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural"><phoneme alphabet="ipa" ph="koɾɐsɐ̃w">coração</phoneme></voice></speak>',
    '<speak><sub alias="coração">coração</sub></speak>',
])
def test_supported_ssml_preserves_same_spoken_text(ssml: str) -> None:
    assert_word_audio_matches_word(replace_ssml(make_record(), ssml), "coração")


def test_ssml_preserves_escaped_text_and_element_tails() -> None:
    text = "café & chá"
    asset = replace_ssml(make_record(word=text), "<speak><prosody>café</prosody> &amp; chá</speak>")

    assert_word_audio_matches_word(asset, text)
