"""Tests for Phase 4 voice registry and Azure speech settings."""

from __future__ import annotations

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_voice_registry import (
    VOICE_REGISTRY_VERSION,
    VoiceSelectionError,
    get_voice_registry,
    select_voice,
)
from multilang.settings import Settings


def test_voice_registry_resolves_supported_languages() -> None:
    registry = get_voice_registry()

    assert set(registry) == {
        SupportedLanguage.PT,
        SupportedLanguage.ES,
        SupportedLanguage.EN,
        SupportedLanguage.FR,
        SupportedLanguage.DE,
        SupportedLanguage.IT,
        SupportedLanguage.PL,
        SupportedLanguage.TR,
        SupportedLanguage.RO,
        SupportedLanguage.RU,
        SupportedLanguage.NL,
    }

    for language in registry:
        selection = select_voice(language)
        assert selection.language is language
        assert selection.voice_id
        assert selection.locale
        assert selection.registry_version == VOICE_REGISTRY_VERSION
        assert selection.fallback_used is False


def test_voice_registry_uses_deterministic_fallback_order() -> None:
    same_locale_fallback = select_voice(
        SupportedLanguage.NL,
        available_voice_ids={"nl-NL-MaartenNeural", "nl-BE-DenaNeural"},
    )
    alternate_locale_fallback = select_voice(
        SupportedLanguage.NL,
        available_voice_ids={"nl-BE-DenaNeural"},
    )

    assert same_locale_fallback.voice_id == "nl-NL-MaartenNeural"
    assert same_locale_fallback.locale == "nl-NL"
    assert same_locale_fallback.fallback_used is True

    assert alternate_locale_fallback.voice_id == "nl-BE-DenaNeural"
    assert alternate_locale_fallback.locale == "nl-BE"
    assert alternate_locale_fallback.fallback_used is True

    with pytest.raises(VoiceSelectionError):
        select_voice(SupportedLanguage.NL, available_voice_ids={"en-US-JennyNeural"})


def test_voice_registry_prefers_english_andrew_dragon_hd_voice() -> None:
    selection = select_voice(SupportedLanguage.EN)

    assert selection.voice_id == "en-US-Andrew:DragonHDLatestNeural"
    assert selection.locale == "en-US"


def test_voice_registry_uses_requested_preferred_voices() -> None:
    assert select_voice(SupportedLanguage.DE).voice_id == "de-DE-ConradNeural"
    assert select_voice(SupportedLanguage.ES).voice_id == "es-ES-TristanMultilingualNeural"
    assert select_voice(SupportedLanguage.FR).voice_id == "fr-FR-Remy:DragonHDLatestNeural"
    assert select_voice(SupportedLanguage.IT).voice_id == "it-IT-GiuseppeMultilingualNeural"
    assert select_voice(SupportedLanguage.RU).voice_id == "ru-RU-DmitryNeural"


def test_settings_expose_azure_speech_configuration() -> None:
    settings = Settings(
        _env_file=None,
        azure_speech_key="speech-key",
        azure_speech_region="westeurope",
    )

    assert settings.azure_speech_key == "speech-key"
    assert settings.azure_speech_region == "westeurope"
    assert settings.azure_speech_output_format == "audio-24khz-48kbitrate-mono-mp3"
    assert settings.audio_storage_dir.name == "audio"
    assert settings.audio_voice_registry_version == VOICE_REGISTRY_VERSION


def test_settings_expose_elevenlabs_configuration() -> None:
    settings = Settings(
        _env_file=None,
        audio_provider="elevenlabs",
        elevenlabs_api_key="eleven-key",
        elevenlabs_voice_id="voice-123",
    )

    assert settings.audio_provider == "elevenlabs"
    assert settings.elevenlabs_api_key == "eleven-key"
    assert settings.elevenlabs_api_key_2 is None
    assert settings.elevenlabs_api_key_3 is None
    assert settings.elevenlabs_api_key_4 is None
    assert settings.elevenlabs_api_keys == []
    assert settings.elevenlabs_voice_id == "voice-123"
    assert settings.elevenlabs_model_id == "eleven_multilingual_v2"
    assert settings.elevenlabs_output_format == "mp3_44100_128"


def test_settings_expose_audio_fallback_providers() -> None:
    settings = Settings(
        _env_file=None,
        audio_provider="azure",
        audio_fallback_providers=["elevenlabs"],
    )

    assert settings.audio_fallback_providers == ["elevenlabs"]


def test_settings_expose_multiple_elevenlabs_keys() -> None:
    settings = Settings(
        _env_file=None,
        elevenlabs_api_key="key-1",
        elevenlabs_api_key_2="key-2",
        elevenlabs_api_key_3="key-3",
        elevenlabs_api_key_4="key-4",
        elevenlabs_api_keys=["key-5", "key-6"],
    )

    assert settings.elevenlabs_api_key == "key-1"
    assert settings.elevenlabs_api_key_2 == "key-2"
    assert settings.elevenlabs_api_key_3 == "key-3"
    assert settings.elevenlabs_api_key_4 == "key-4"
    assert settings.elevenlabs_api_keys == ["key-5", "key-6"]
