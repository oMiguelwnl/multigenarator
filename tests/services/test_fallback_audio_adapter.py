"""Tests for audio provider fallback orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.audio_voice_registry import VoiceSelection
from multilang.services.fallback_audio_adapter import FallbackAudioAdapter


class FailingAudioAdapter:
    provider = AudioProvider.AZURE
    audio_format = AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3

    def available_voice_ids(self) -> set[str] | None:
        return None

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        return VoiceSelection(
            language=language,
            voice_id="azure-voice",
            locale="pl-PL",
            registry_version="azure-test",
        )

    def synthesize(self, **kwargs: object) -> AudioSynthesisResponse:
        raise RuntimeError("quota exceeded")


class VoiceSelectionFailingAdapter(FailingAudioAdapter):
    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        raise RuntimeError("voice inventory failed")


class WorkingElevenLabsAdapter:
    provider = AudioProvider.ELEVENLABS
    audio_format = AudioFormat.MP3_44100_128

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def available_voice_ids(self) -> set[str] | None:
        return None

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        return VoiceSelection(
            language=language,
            voice_id="eleven-voice",
            locale="pl-PL",
            registry_version="eleven-test",
        )

    def synthesize(self, **kwargs: object) -> AudioSynthesisResponse:
        self.calls.append(kwargs)
        output_path = kwargs["output_path"]
        assert isinstance(output_path, Path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"ID3-fallback")
        return AudioSynthesisResponse(storage_path=output_path, byte_size=12, duration_ms=500)


def test_fallback_audio_adapter_uses_next_provider_when_primary_synthesis_fails(tmp_path: Path) -> None:
    elevenlabs = WorkingElevenLabsAdapter()
    adapter = FallbackAudioAdapter([FailingAudioAdapter(), elevenlabs])
    selection = adapter.select_voice(SupportedLanguage.PL)

    response = adapter.synthesize(
        ssml_text="czesc",
        voice_id=selection.voice_id,
        locale=selection.locale,
        output_path=tmp_path / "audio.mp3",
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )

    assert response.provider is AudioProvider.ELEVENLABS
    assert response.voice_id is None
    assert response.locale is None
    assert response.audio_format is None
    assert response.fallback_used is True
    assert elevenlabs.calls[0]["audio_format"] == "mp3_44100_128"


def test_fallback_audio_adapter_skips_provider_when_voice_selection_fails(tmp_path: Path) -> None:
    elevenlabs = WorkingElevenLabsAdapter()
    adapter = FallbackAudioAdapter([VoiceSelectionFailingAdapter(), elevenlabs])
    selection = adapter.select_voice(SupportedLanguage.PL)

    response = adapter.synthesize(
        ssml_text="czesc",
        voice_id=selection.voice_id,
        locale=selection.locale,
        output_path=tmp_path / "audio.mp3",
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )

    assert response.provider is AudioProvider.ELEVENLABS
    assert response.fallback_used is False


def test_fallback_audio_adapter_requires_at_least_one_adapter() -> None:
    with pytest.raises(ValueError, match="at least one"):
        FallbackAudioAdapter([])
