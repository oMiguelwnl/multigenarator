"""Tests for the ElevenLabs Speech adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.elevenlabs_speech_adapter import (
    ElevenLabsSpeechAdapter,
    ElevenLabsSpeechAdapterError,
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


def test_elevenlabs_adapter_posts_plain_text_and_writes_mp3(tmp_path: Path) -> None:
    requests = []

    def fake_urlopen(request, timeout: int = 30):
        requests.append(request)
        return _FakeAudioResponse(b"ID3-elevenlabs-bytes")

    adapter = ElevenLabsSpeechAdapter(
        Settings(
            _env_file=None,
            elevenlabs_api_key="test-key",
            elevenlabs_voice_id="voice-123",
            elevenlabs_model_id="eleven_multilingual_v2",
        ),
        urlopen_func=fake_urlopen,
    )
    output_path = tmp_path / "audio.mp3"

    response = adapter.synthesize(
        ssml_text='<speak version="1.0"><prosody rate="-10%">Dzien dobry</prosody></speak>',
        voice_id="voice-123",
        locale="pl-PL",
        output_path=output_path,
        audio_format="mp3_44100_128",
    )

    assert response.storage_path == output_path
    assert response.byte_size == len(b"ID3-elevenlabs-bytes")
    assert output_path.read_bytes() == b"ID3-elevenlabs-bytes"
    assert requests[0].full_url == "https://api.elevenlabs.io/v1/text-to-speech/voice-123?output_format=mp3_44100_128"
    assert json.loads((requests[0].data or b"").decode("utf-8")) == {
        "text": "Dzien dobry",
        "model_id": "eleven_multilingual_v2",
    }
    assert requests[0].get_header("Xi-api-key") == "test-key"


def test_elevenlabs_adapter_selects_configured_voice() -> None:
    adapter = ElevenLabsSpeechAdapter(
        Settings(_env_file=None, elevenlabs_voice_id="voice-123")
    )

    selection = adapter.select_voice(SupportedLanguage.PL)

    assert selection.voice_id == "voice-123"
    assert selection.locale == "pl-PL"
    assert selection.registry_version == "elevenlabs-premade-v1-eleven_multilingual_v2"


def test_elevenlabs_adapter_uses_default_voice_for_language() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.PL)

    assert selection.voice_id == "ErXwobaYiN019PkySvjV"
    assert selection.locale == "pl-PL"


def test_elevenlabs_adapter_uses_default_voice_for_norwegian_bokmal() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.NB)

    assert selection.voice_id == "TxGEqnHWrfWFTfGW9XjX"
    assert selection.locale == "nb-NO"


def test_elevenlabs_adapter_uses_default_voice_for_danish() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.DA)

    assert selection.voice_id == "TxGEqnHWrfWFTfGW9XjX"
    assert selection.locale == "da-DK"


def test_elevenlabs_adapter_uses_default_voice_for_swedish() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.SV)

    assert selection.voice_id == "TxGEqnHWrfWFTfGW9XjX"
    assert selection.locale == "sv-SE"


def test_elevenlabs_adapter_uses_default_voice_for_finnish() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.FI)

    assert selection.voice_id == "TxGEqnHWrfWFTfGW9XjX"
    assert selection.locale == "fi-FI"


def test_elevenlabs_adapter_uses_default_voice_for_czech() -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    selection = adapter.select_voice(SupportedLanguage.CS)

    assert selection.voice_id == "TxGEqnHWrfWFTfGW9XjX"
    assert selection.locale == "cs-CZ"


def test_elevenlabs_adapter_requires_credentials(tmp_path: Path) -> None:
    adapter = ElevenLabsSpeechAdapter(Settings(_env_file=None))

    with pytest.raises(ElevenLabsSpeechAdapterError, match="MULTILANG_ELEVENLABS_API_KEY"):
        adapter.synthesize(
            ssml_text="hello",
            voice_id="unconfigured",
            locale="en-US",
            output_path=tmp_path / "audio.mp3",
            audio_format="mp3_44100_128",
        )


def test_elevenlabs_adapter_tries_next_key_when_one_fails(tmp_path: Path) -> None:
    requests = []

    def fake_urlopen(request, timeout: int = 30):
        requests.append(request)
        if request.get_header("Xi-api-key") == "bad-key":
            raise RuntimeError("quota exceeded")
        return _FakeAudioResponse(b"ID3-second-key")

    adapter = ElevenLabsSpeechAdapter(
        Settings(
            _env_file=None,
            elevenlabs_api_key="bad-key",
            elevenlabs_api_key_2="good-key",
            elevenlabs_voice_id="voice-123",
        ),
        urlopen_func=fake_urlopen,
    )

    response = adapter.synthesize(
        ssml_text="Dzien dobry",
        voice_id="voice-123",
        locale="pl-PL",
        output_path=tmp_path / "audio.mp3",
        audio_format="mp3_44100_128",
    )

    assert response.byte_size == len(b"ID3-second-key")
    assert [request.get_header("Xi-api-key") for request in requests] == ["bad-key", "good-key"]


def test_elevenlabs_adapter_uses_same_key_until_it_fails(tmp_path: Path) -> None:
    used_keys: list[str | None] = []

    def fake_urlopen(request, timeout: int = 30):
        used_keys.append(request.get_header("Xi-api-key"))
        return _FakeAudioResponse(b"ID3-audio")

    adapter = ElevenLabsSpeechAdapter(
        Settings(
            _env_file=None,
            elevenlabs_api_key="key-1",
            elevenlabs_api_key_2="key-2",
            elevenlabs_api_key_3="key-3",
            elevenlabs_api_key_4="key-4",
            elevenlabs_voice_id="voice-123",
        ),
        urlopen_func=fake_urlopen,
    )

    for index in range(3):
        adapter.synthesize(
            ssml_text="Dzien dobry",
            voice_id="voice-123",
            locale="pl-PL",
            output_path=tmp_path / f"audio-{index}.mp3",
            audio_format="mp3_44100_128",
        )

    assert used_keys == ["key-1", "key-1", "key-1"]


def test_elevenlabs_adapter_moves_to_next_key_after_current_key_fails(tmp_path: Path) -> None:
    used_keys: list[str | None] = []
    fail_key_1 = False
    fail_key_2 = False

    def fake_urlopen(request, timeout: int = 30):
        nonlocal fail_key_1, fail_key_2
        key = request.get_header("Xi-api-key")
        used_keys.append(key)
        if key == "key-1" and fail_key_1:
            raise RuntimeError("key 1 quota exceeded")
        if key == "key-2" and fail_key_2:
            raise RuntimeError("key 2 quota exceeded")
        return _FakeAudioResponse(f"ID3-{key}".encode("utf-8"))

    adapter = ElevenLabsSpeechAdapter(
        Settings(
            _env_file=None,
            elevenlabs_api_key="key-1",
            elevenlabs_api_key_2="key-2",
            elevenlabs_api_key_3="key-3",
            elevenlabs_voice_id="voice-123",
        ),
        urlopen_func=fake_urlopen,
    )

    adapter.synthesize(
        ssml_text="Dzien dobry",
        voice_id="voice-123",
        locale="pl-PL",
        output_path=tmp_path / "audio-1.mp3",
        audio_format="mp3_44100_128",
    )
    fail_key_1 = True
    adapter.synthesize(
        ssml_text="Dzien dobry",
        voice_id="voice-123",
        locale="pl-PL",
        output_path=tmp_path / "audio-2.mp3",
        audio_format="mp3_44100_128",
    )
    fail_key_2 = True
    adapter.synthesize(
        ssml_text="Dzien dobry",
        voice_id="voice-123",
        locale="pl-PL",
        output_path=tmp_path / "audio-3.mp3",
        audio_format="mp3_44100_128",
    )

    assert used_keys == ["key-1", "key-1", "key-2", "key-2", "key-3"]
