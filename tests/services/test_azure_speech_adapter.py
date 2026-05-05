"""Tests for the shipped Azure Speech adapter."""

from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from multilang.services.azure_speech_adapter import AzureSpeechAdapter, AzureSpeechAdapterError, build_azure_ssml
from multilang.settings import Settings


class _FakeVoiceResponse:
    def __init__(self, payload: list[dict[str, str]]) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> _FakeVoiceResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeSpeechConfig:
    def __init__(self, *, subscription: str, region: str) -> None:
        self.subscription = subscription
        self.region = region
        self.speech_synthesis_language: str | None = None
        self.speech_synthesis_voice_name: str | None = None
        self.output_format = None

    def set_speech_synthesis_output_format(self, output_format: object) -> None:
        self.output_format = output_format


class _FakeAudioOutputConfig:
    def __init__(self, *, filename: str) -> None:
        self.filename = filename


class _FakeResult:
    def __init__(self, *, reason: object, audio_data: bytes, audio_duration: object) -> None:
        self.reason = reason
        self.audio_data = audio_data
        self.audio_duration = audio_duration


class _FakeFuture:
    def __init__(self, result: _FakeResult) -> None:
        self._result = result

    def get(self) -> _FakeResult:
        return self._result


class _FakeSpeechSynthesizer:
    latest_config: _FakeSpeechConfig | None = None
    latest_filename: str | None = None
    latest_ssml: str | None = None
    next_result = _FakeResult(
        reason="completed",
        audio_data=b"ID3-provider-bytes",
        audio_duration=timedelta(milliseconds=875),
    )

    def __init__(self, *, speech_config: _FakeSpeechConfig, audio_config: _FakeAudioOutputConfig) -> None:
        self.speech_config = speech_config
        self.audio_config = audio_config
        _FakeSpeechSynthesizer.latest_config = speech_config
        _FakeSpeechSynthesizer.latest_filename = audio_config.filename

    def speak_ssml_async(self, ssml_text: str) -> _FakeFuture:
        _FakeSpeechSynthesizer.latest_ssml = ssml_text
        Path(self.audio_config.filename).write_bytes(self.next_result.audio_data)
        return _FakeFuture(self.next_result)


_FAKE_SPEECHSDK = SimpleNamespace(
    SpeechConfig=_FakeSpeechConfig,
    SpeechSynthesizer=_FakeSpeechSynthesizer,
    SpeechSynthesisOutputFormat=SimpleNamespace(Audio24Khz48KBitRateMonoMp3="mp3-enum"),
    ResultReason=SimpleNamespace(SynthesizingAudioCompleted="completed"),
    CancellationDetails=SimpleNamespace(
        from_result=lambda result: SimpleNamespace(
            reason="canceled", error_code="BadRequest", error_details="boom"
        )
    ),
    audio=SimpleNamespace(AudioOutputConfig=_FakeAudioOutputConfig),
)


def test_azure_speech_adapter_lists_available_voice_ids_once() -> None:
    calls: list[str] = []

    def fake_urlopen(request, timeout: int = 10):
        calls.append(request.full_url)
        return _FakeVoiceResponse(
            [{"ShortName": "en-US-JennyNeural"}, {"ShortName": "en-US-GuyNeural"}]
        )

    adapter = AzureSpeechAdapter(
        Settings(azure_speech_key="key", azure_speech_region="eastus"),
        urlopen_func=fake_urlopen,
    )

    first = adapter.available_voice_ids()
    second = adapter.available_voice_ids()

    assert first == {"en-US-JennyNeural", "en-US-GuyNeural"}
    assert second == first
    assert calls == [
        "https://eastus.tts.speech.microsoft.com/cognitiveservices/voices/list"
    ]


def test_azure_speech_adapter_synthesizes_ssml_to_expected_file(tmp_path: Path) -> None:
    output_path = tmp_path / "audio" / "word.mp3"
    adapter = AzureSpeechAdapter(
        Settings(azure_speech_key="key", azure_speech_region="eastus"),
        speechsdk_module=_FAKE_SPEECHSDK,
    )

    response = adapter.synthesize(
        ssml_text="<speak>Hello & \"Azure\"</speak>",
        voice_id="en-US-JennyNeural",
        locale="en-US",
        output_path=output_path,
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )

    assert response.storage_path == output_path
    assert response.byte_size == len(b"ID3-provider-bytes")
    assert response.duration_ms == 875
    assert output_path.read_bytes() == b"ID3-provider-bytes"
    assert _FakeSpeechSynthesizer.latest_config is not None
    assert _FakeSpeechSynthesizer.latest_config.speech_synthesis_voice_name == "en-US-JennyNeural"
    assert _FakeSpeechSynthesizer.latest_config.speech_synthesis_language == "en-US"
    assert _FakeSpeechSynthesizer.latest_config.output_format == "mp3-enum"
    assert _FakeSpeechSynthesizer.latest_ssml is not None
    assert 'xmlns="http://www.w3.org/2001/10/synthesis"' in _FakeSpeechSynthesizer.latest_ssml
    assert 'xml:lang="en-US"' in _FakeSpeechSynthesizer.latest_ssml
    assert '<voice name="en-US-JennyNeural">Hello &amp; &quot;Azure&quot;</voice>' in _FakeSpeechSynthesizer.latest_ssml


def test_azure_speech_adapter_requires_credentials_for_synthesis(tmp_path: Path) -> None:
    adapter = AzureSpeechAdapter(
        Settings(_env_file=None, azure_speech_key=None, azure_speech_region=None),
        speechsdk_module=_FAKE_SPEECHSDK,
    )

    with pytest.raises(AzureSpeechAdapterError, match="MULTILANG_AZURE_SPEECH_KEY"):
        adapter.synthesize(
            ssml_text="<speak>Hello</speak>",
            voice_id="en-US-JennyNeural",
            locale="en-US",
            output_path=tmp_path / "audio.mp3",
            audio_format="audio-24khz-48kbitrate-mono-mp3",
        )


def test_build_azure_ssml_preserves_safe_prosody_from_legacy_speak() -> None:
    ssml = build_azure_ssml(
        text='<speak version="1.0"><prosody rate="-10%" pitch="+8%" volume="+20%">run</prosody></speak>',
        voice_id="en-US-JennyNeural",
        locale="en-US",
    )

    assert '<voice name="en-US-JennyNeural"><prosody rate="-10%" pitch="+8%" volume="+20%">run</prosody></voice>' in ssml


def test_azure_speech_adapter_surfaces_cancellation_details(tmp_path: Path) -> None:
    _FakeSpeechSynthesizer.next_result = _FakeResult(
        reason="canceled",
        audio_data=b"",
        audio_duration=None,
    )
    adapter = AzureSpeechAdapter(
        Settings(azure_speech_key="key", azure_speech_region="eastus"),
        speechsdk_module=_FAKE_SPEECHSDK,
    )

    with pytest.raises(
        AzureSpeechAdapterError,
        match="reason=canceled; error_code=BadRequest; details=boom",
    ):
        adapter.synthesize(
            ssml_text="hello",
            voice_id="en-US-JennyNeural",
            locale="en-US",
            output_path=tmp_path / "audio.mp3",
            audio_format="audio-24khz-48kbitrate-mono-mp3",
        )

    _FakeSpeechSynthesizer.next_result = _FakeResult(
        reason="completed",
        audio_data=b"ID3-provider-bytes",
        audio_duration=timedelta(milliseconds=875),
    )
