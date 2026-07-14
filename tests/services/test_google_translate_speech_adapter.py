"""Tests for the Google Translate Speech adapter."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.google_translate_speech_adapter import (
    GoogleTranslateSpeechAdapter,
    GoogleTranslateSpeechAdapterError,
)
from multilang.settings import Settings


class _FakeAudioResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> _FakeAudioResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_google_translate_adapter_requests_tts_and_writes_mp3(tmp_path: Path) -> None:
    requests = []

    def fake_urlopen(request, timeout: int = 30):
        requests.append(request)
        return _FakeAudioResponse(b"ID3-google-tts-bytes")

    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None), urlopen_func=fake_urlopen)
    output_path = tmp_path / "audio.mp3"

    response = adapter.synthesize(
        ssml_text='<speak version="1.0"><prosody rate="-10%">Arma virumque cano.</prosody></speak>',
        voice_id="la",
        locale="la",
        output_path=output_path,
        audio_format="mp3",
    )

    parsed = urlparse(requests[0].full_url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "translate.google.com"
    assert parsed.path == "/translate_tts"
    assert query["tl"] == ["la"]
    assert query["q"] == ["Arma virumque cano."]
    assert requests[0].get_method() == "GET"
    assert output_path.read_bytes() == b"ID3-google-tts-bytes"
    assert response.storage_path == output_path
    assert response.byte_size == len(b"ID3-google-tts-bytes")
    assert response.voice_id == "la"
    assert response.locale == "la"


def test_google_translate_adapter_selects_language_code_voice() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.IT)

    assert selection.voice_id == "it"
    assert selection.locale == "it"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_selects_norwegian_bokmal_language() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.NB)

    assert selection.voice_id == "no"
    assert selection.locale == "no"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_selects_danish_language() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.DA)

    assert selection.voice_id == "da"
    assert selection.locale == "da"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_selects_swedish_language() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.SV)

    assert selection.voice_id == "sv"
    assert selection.locale == "sv"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_selects_finnish_language() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.FI)

    assert selection.voice_id == "fi"
    assert selection.locale == "fi"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_selects_czech_language() -> None:
    adapter = GoogleTranslateSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.CS)

    assert selection.voice_id == "cs"
    assert selection.locale == "cs"
    assert selection.registry_version == "google-translate-tts-v1"


def test_google_translate_adapter_rejects_empty_or_non_mp3_audio(tmp_path: Path) -> None:
    adapter = GoogleTranslateSpeechAdapter(
        Settings(_env_file=None),
        urlopen_func=lambda request, timeout=30: _FakeAudioResponse(b""),
    )

    with pytest.raises(GoogleTranslateSpeechAdapterError, match="mp3 output only"):
        adapter.synthesize(
            ssml_text="Arma",
            voice_id="la",
            locale="la",
            output_path=tmp_path / "audio.wav",
            audio_format="wav",
        )

    with pytest.raises(GoogleTranslateSpeechAdapterError, match="returned empty audio"):
        adapter.synthesize(
            ssml_text="Arma",
            voice_id="la",
            locale="la",
            output_path=tmp_path / "audio.mp3",
            audio_format="mp3",
        )
