"""Contract tests for Phase 4 audio records."""

from __future__ import annotations

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)


def make_record(**overrides: object) -> AudioAssetRecord:
    payload: dict[str, object] = {
        "job_id": "job-123",
        "item_key": "item-1",
        "asset_kind": AudioAssetKind.WORD,
        "display_text": "coração",
        "normalized_input": NormalizedTtsInput(
            display_text="coração",
            tts_text="coracao",
            ssml_text="<speak version=\"1.0\">coracao</speak>",
        ),
        "provenance": AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="pt-BR-FranciscaNeural",
            locale="pt-BR",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash="text-hash",
            ssml_hash="ssml-hash",
            storage_path="audio/word/text-hash.mp3",
            byte_size=4096,
            duration_ms=1200,
            status=AudioSynthesisStatus.SYNTHESIZED,
            fallback_used=False,
        ),
    }
    payload.update(overrides)
    return AudioAssetRecord(**payload)


def test_audio_asset_record_keeps_separate_word_and_sentence_identity() -> None:
    word_record = make_record(asset_kind=AudioAssetKind.WORD)
    sentence_record = make_record(
        asset_kind=AudioAssetKind.SENTENCE,
        display_text="Eu sinto isso no coração.",
        normalized_input=NormalizedTtsInput(
            display_text="Eu sinto isso no coração.",
            tts_text="Eu sinto isso no coracao.",
            ssml_text="<speak version=\"1.0\">Eu sinto isso no coracao.</speak>",
        ),
    )

    assert word_record.identity_key == ("job-123", "item-1", AudioAssetKind.WORD)
    assert sentence_record.identity_key == (
        "job-123",
        "item-1",
        AudioAssetKind.SENTENCE,
    )
    assert word_record.asset_kind is AudioAssetKind.WORD
    assert sentence_record.asset_kind is AudioAssetKind.SENTENCE


def test_audio_asset_record_keeps_audio_provenance_and_integrity_fields() -> None:
    record = make_record()

    assert record.provenance.provider is AudioProvider.AZURE
    assert record.provenance.voice_id == "pt-BR-FranciscaNeural"
    assert record.provenance.locale == "pt-BR"
    assert record.provenance.format is AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3
    assert record.provenance.text_hash == "text-hash"
    assert record.provenance.ssml_hash == "ssml-hash"
    assert record.provenance.storage_path == "audio/word/text-hash.mp3"
    assert record.provenance.byte_size == 4096
    assert record.provenance.duration_ms == 1200
    assert record.provenance.status is AudioSynthesisStatus.SYNTHESIZED
    assert record.provenance.fallback_used is False


def test_audio_asset_record_separates_tts_text_from_display_text() -> None:
    record = make_record(
        display_text="ação",
        normalized_input=NormalizedTtsInput(
            display_text="ação",
            tts_text="acao",
            ssml_text="<speak version=\"1.0\">acao</speak>",
        ),
    )

    assert record.display_text == "ação"
    assert record.normalized_input.display_text == "ação"
    assert record.normalized_input.tts_text == "acao"
    assert record.normalized_input.display_text != record.normalized_input.tts_text
    assert record.normalized_input.text_hash
    assert record.normalized_input.ssml_hash
