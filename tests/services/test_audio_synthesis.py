"""Tests for Phase 4 audio synthesis boundaries."""

from __future__ import annotations

from pathlib import Path

from multilang.domain.audio import AudioAssetKind, AudioFormat, AudioProvider, AudioSynthesisStatus
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.services.audio_synthesis import (
    AudioSynthesisAdapter,
    AudioSynthesisBundle,
    AudioSynthesisResponse,
    AudioSynthesisService,
)
from multilang.services.audio_voice_registry import VoiceSelection
from multilang.settings import Settings


def make_text_record(**overrides: object) -> TextQualityRecord:
    payload: dict[str, object] = {
        "job_id": "job-123",
        "item_key": "item-1",
        "lexical_candidate_id": "lex-123",
        "example_sentence": "I read every night.",
        "translation_text": "Eu leio toda noite.",
        "generation_status": TextGenerationStatus.GENERATED,
        "validation_status": ValidationStatus.PASSED,
        "review_status": ReviewStatus.ACCEPTED,
        "repair_attempt_count": 0,
        "confidence_score": 0.96,
        "confidence_label": ConfidenceLabel.HIGH,
        "validation_flags": [],
        "review_reason": None,
        "sentence_provenance": TextProvenance(source="generator", provider="local"),
        "translation_provenance": TextProvenance(source="translator", provider="local"),
    }
    payload.update(overrides)
    return TextQualityRecord(**payload)


class FakeAudioAdapter(AudioSynthesisAdapter):
    def __init__(self, base_dir: Path, *, available_voice_ids: set[str] | None = None) -> None:
        self.base_dir = base_dir
        self._available_voice_ids = available_voice_ids
        self.calls: list[tuple[str, str, str, Path]] = []

    def available_voice_ids(self) -> set[str] | None:
        return self._available_voice_ids

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        self.calls.append((ssml_text, voice_id, locale, output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(f"{voice_id}:{audio_format}:{ssml_text}".encode("utf-8"))
        return AudioSynthesisResponse(storage_path=output_path, byte_size=output_path.stat().st_size, duration_ms=875)


class MissingFileAdapter(FakeAudioAdapter):
    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        self.calls.append((ssml_text, voice_id, locale, output_path))
        return AudioSynthesisResponse(storage_path=output_path, byte_size=0, duration_ms=None)


class RaisingAdapter(FakeAudioAdapter):
    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        raise RuntimeError("azure canceled")


class FakeElevenLabsAdapter(FakeAudioAdapter):
    provider = AudioProvider.ELEVENLABS
    audio_format = AudioFormat.MP3_44100_128

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        return VoiceSelection(
            language=language,
            voice_id="elevenlabs-voice",
            locale="pl-PL",
            registry_version="elevenlabs-test",
            fallback_used=False,
        )


def build_service(tmp_path: Path, *, available_voice_ids: set[str] | None = None) -> AudioSynthesisService:
    return AudioSynthesisService(
        adapter=FakeAudioAdapter(tmp_path, available_voice_ids=available_voice_ids),
        settings=Settings(audio_storage_dir=tmp_path / "audio"),
    )


def test_audio_synthesis_service_rejects_review_required_text(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    review_required = make_text_record(review_status=ReviewStatus.REVIEW_REQUIRED)

    bundle = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=review_required,
    )

    assert bundle.word_asset.provenance.status is AudioSynthesisStatus.FAILED
    assert bundle.sentence_asset.provenance.status is AudioSynthesisStatus.FAILED
    assert bundle.word_asset.provenance.byte_size == 0
    assert bundle.sentence_asset.provenance.byte_size == 0


def test_audio_synthesis_service_persists_fallback_used(tmp_path: Path) -> None:
    service = build_service(tmp_path, available_voice_ids={"nl-NL-MaartenNeural", "nl-BE-DenaNeural"})

    bundle = service.synthesize_item(
        language=SupportedLanguage.NL,
        display_word="lezen",
        text_record=make_text_record(
            example_sentence="Ik lees elke avond.",
            translation_text="I read every evening.",
        ),
    )

    assert bundle.word_asset.provenance.status is AudioSynthesisStatus.SYNTHESIZED
    assert bundle.word_asset.provenance.voice_id == "nl-NL-MaartenNeural"
    assert bundle.word_asset.provenance.fallback_used is True
    assert bundle.sentence_asset.provenance.fallback_used is True


def test_audio_synthesis_service_reuses_deterministic_storage_keys(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    record = make_text_record(example_sentence="I   read every night.")

    first = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=record,
    )
    second = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=record,
    )

    assert first.word_asset.provenance.storage_path == second.word_asset.provenance.storage_path
    assert first.sentence_asset.provenance.storage_path == second.sentence_asset.provenance.storage_path
    assert first.word_asset.display_text == "read"
    assert first.word_asset.normalized_input.tts_text == "read"
    assert first.sentence_asset.normalized_input.tts_text == "I read every night."


def test_audio_synthesis_service_rejects_missing_or_empty_media_files(tmp_path: Path) -> None:
    service = AudioSynthesisService(
        adapter=MissingFileAdapter(tmp_path),
        settings=Settings(audio_storage_dir=tmp_path / "audio"),
    )

    bundle = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=make_text_record(),
    )

    assert bundle.word_asset.provenance.status is AudioSynthesisStatus.FAILED
    assert bundle.word_asset.provenance.byte_size == 0
    assert bundle.sentence_asset.provenance.status is AudioSynthesisStatus.FAILED


def test_audio_synthesis_service_marks_adapter_errors_as_failed(tmp_path: Path) -> None:
    service = AudioSynthesisService(
        adapter=RaisingAdapter(tmp_path),
        settings=Settings(audio_storage_dir=tmp_path / "audio"),
    )

    bundle = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=make_text_record(),
    )

    assert bundle.word_asset.provenance.status is AudioSynthesisStatus.FAILED
    assert bundle.sentence_asset.provenance.status is AudioSynthesisStatus.FAILED


def test_audio_synthesis_service_records_elevenlabs_provider_and_format(tmp_path: Path) -> None:
    service = AudioSynthesisService(
        adapter=FakeElevenLabsAdapter(tmp_path),
        settings=Settings(audio_storage_dir=tmp_path / "audio"),
    )

    bundle = service.synthesize_item(
        language=SupportedLanguage.PL,
        display_word="dom",
        text_record=make_text_record(example_sentence="To jest duzy dom."),
    )

    assert bundle.word_asset.provenance.provider is AudioProvider.ELEVENLABS
    assert bundle.word_asset.provenance.format is AudioFormat.MP3_44100_128
    assert bundle.word_asset.provenance.voice_id == "elevenlabs-voice"
    assert "elevenlabs-test" in bundle.word_asset.provenance.storage_path


def test_audio_synthesis_service_returns_separate_word_and_sentence_assets(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    bundle = service.synthesize_item(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=make_text_record(example_sentence="I read before bed."),
    )

    assert isinstance(bundle, AudioSynthesisBundle)
    assert bundle.word_asset.asset_kind is AudioAssetKind.WORD
    assert bundle.sentence_asset.asset_kind is AudioAssetKind.SENTENCE
    assert bundle.word_asset.provenance.storage_path != bundle.sentence_asset.provenance.storage_path
    assert bundle.word_asset.display_text == "read"
    assert bundle.sentence_asset.display_text == "I read before bed."


def test_audio_synthesis_service_applies_prominent_prosody_to_word_only(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    bundle = service.prepare_item_assets(
        language=SupportedLanguage.EN,
        display_word="read",
        text_record=make_text_record(example_sentence="I read before bed."),
    )

    word_ssml = bundle.word_asset.normalized_input.ssml_text or ""
    sentence_ssml = bundle.sentence_asset.normalized_input.ssml_text or ""
    assert '<prosody rate="-10%" pitch="+8%" volume="+20%">read</prosody>' in word_ssml
    assert "<prosody" not in sentence_ssml
