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


def test_settings_expose_azure_speech_configuration() -> None:
    settings = Settings(
        azure_speech_key="speech-key",
        azure_speech_region="westeurope",
    )

    assert settings.azure_speech_key == "speech-key"
    assert settings.azure_speech_region == "westeurope"
    assert settings.azure_speech_output_format == "audio-24khz-48kbitrate-mono-mp3"
    assert settings.audio_storage_dir.name == "audio"
    assert settings.audio_voice_registry_version == VOICE_REGISTRY_VERSION
