"""Tests for Latin audio generation fallback orchestration."""

from __future__ import annotations

from pathlib import Path

from multilang.services.latin_audio_generation import LatinAudioGenerationService


def test_latin_audio_generation_uses_google_tts_first() -> None:
    service = LatinAudioGenerationService(
        {
            "google-translate-tts": lambda text, kind, _path: {
                "provider": "google-translate-tts",
                "provider_version": "google-translate-tts-la",
                "voice": "la",
                "pronunciation_policy": "google_latin",
                "storage_path": f"audio/{kind}-{text}.mp3",
            }
        }
    )

    artifact = service.synthesize("amat", "word", Path("unused.mp3"))

    assert artifact.provider == "google-translate-tts"
    assert artifact.fallback_reason is None


def test_latin_audio_generation_falls_back_to_elevenlabs() -> None:
    service = LatinAudioGenerationService(
        {
            "elevenlabs-italian": lambda text, kind, _path: {
                "provider": "elevenlabs-italian",
                "provider_version": "eleven_multilingual_v2",
                "voice": "it-IT",
                "pronunciation_policy": "italian_multilingual_approx",
                "storage_path": f"audio/{kind}-{text}.mp3",
            }
        }
    )

    artifact = service.synthesize("amat", "word", Path("unused.mp3"))

    assert artifact.provider == "elevenlabs-italian"
    assert artifact.fallback_reason is not None
