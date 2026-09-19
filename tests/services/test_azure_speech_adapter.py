"""Tests for the shipped Azure Speech adapter."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from multilang.services.azure_speech_adapter import (
    AzureSpeechAdapter,
    AzureSpeechAdapterError,
    build_azure_ssml,
)
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

    def __init__(
        self, *, speech_config: _FakeSpeechConfig, audio_config: _FakeAudioOutputConfig
    ) -> None:
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
    SpeechSynthesisOutputFormat=SimpleNamespace(
        Audio24Khz48KBitRateMonoMp3="mp3-enum",
        Riff24Khz16BitMonoPcm="wav-enum",
    ),
    ResultReason=SimpleNamespace(SynthesizingAudioCompleted="completed"),
    CancellationDetails=SimpleNamespace(
        from_result=lambda result: SimpleNamespace(
            reason="canceled", error_code="BadRequest", error_details="boom"
        )
    ),
    audio=SimpleNamespace(AudioOutputConfig=_FakeAudioOutputConfig),
)


@pytest.mark.parametrize(
    "completes,cleanup_failure",
    [
        (True, None),
        (False, None),
        (False, "stop"),
        (False, "disconnect"),
        (True, "disconnect"),
    ],
)
def test_azure_synthesis_obeys_explicit_timeout_without_unbounded_future_get(
    tmp_path,
    completes,
    cleanup_failure,
):
    class Signal:
        def __init__(self):
            self.callback = None

        def connect(self, callback):
            self.callback = callback

        def disconnect(self, callback):
            self.callback = None
            if cleanup_failure == "disconnect":
                raise RuntimeError("SDK cleanup failed")

    class BoundedSynthesizer:
        latest = None

        def __init__(self, *, speech_config, audio_config):
            assert audio_config is None
            self.synthesis_completed = Signal()
            self.synthesis_canceled = Signal()
            self.stopped = False
            BoundedSynthesizer.latest = self

        def speak_ssml_async(self, ssml):
            if completes:
                self.synthesis_completed.callback(
                    SimpleNamespace(result=_FakeSpeechSynthesizer.next_result)
                )
            return SimpleNamespace(get=lambda: pytest.fail("unbounded future get"))

        def stop_speaking_async(self):
            self.stopped = True
            if cleanup_failure == "stop":
                raise RuntimeError("SDK cleanup failed")
            return SimpleNamespace(get=lambda: pytest.fail("unbounded cancellation get"))

    sdk = SimpleNamespace(**{**vars(_FAKE_SPEECHSDK), "SpeechSynthesizer": BoundedSynthesizer})
    adapter = AzureSpeechAdapter(
        Settings(_env_file=None, azure_speech_key="fixture", azure_speech_region="eastus"),
        speechsdk_module=sdk,
    )
    path = tmp_path / "bounded.mp3"
    kwargs = dict(
        ssml_text="<speak>Test</speak>",
        voice_id="en-US-JennyNeural",
        locale="en-US",
        output_path=path,
        audio_format="audio-24khz-48kbitrate-mono-mp3",
        timeout_seconds=0.01,
    )
    if completes:
        result = adapter.synthesize(**kwargs)
        assert path.read_bytes() == _FakeSpeechSynthesizer.next_result.audio_data
        assert result.byte_size == path.stat().st_size
    else:
        with pytest.raises(TimeoutError, match="timed out"):
            adapter.synthesize(**kwargs)
        assert BoundedSynthesizer.latest.stopped
        assert not path.exists()
    assert BoundedSynthesizer.latest.synthesis_completed.callback is None
    assert BoundedSynthesizer.latest.synthesis_canceled.callback is None


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
    assert calls == ["https://eastus.tts.speech.microsoft.com/cognitiveservices/voices/list"]


def test_azure_speech_adapter_synthesizes_ssml_to_expected_file(tmp_path: Path) -> None:
    output_path = tmp_path / "audio" / "word.mp3"
    adapter = AzureSpeechAdapter(
        Settings(azure_speech_key="key", azure_speech_region="eastus"),
        speechsdk_module=_FAKE_SPEECHSDK,
    )

    response = adapter.synthesize(
        ssml_text='<speak>Hello & "Azure"</speak>',
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
    assert (
        '<voice name="en-US-JennyNeural">Hello &amp; &quot;Azure&quot;</voice>'
        in _FakeSpeechSynthesizer.latest_ssml
    )


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


def test_azure_speech_adapter_supports_phase31_wav_format(tmp_path: Path) -> None:
    output_path = tmp_path / "audio" / "word.wav"
    adapter = AzureSpeechAdapter(
        Settings(azure_speech_key="key", azure_speech_region="eastus"),
        speechsdk_module=_FAKE_SPEECHSDK,
    )

    adapter.synthesize(
        ssml_text="안녕하세요",
        voice_id="ko-KR-SunHiNeural",
        locale="ko-KR",
        output_path=output_path,
        audio_format="pcm_s16le_wav",
    )

    assert _FakeSpeechSynthesizer.latest_config is not None
    assert _FakeSpeechSynthesizer.latest_config.output_format == "wav-enum"


def test_build_azure_ssml_preserves_safe_prosody_from_legacy_speak() -> None:
    ssml = build_azure_ssml(
        text='<speak version="1.0"><prosody rate="-10%" pitch="+8%" volume="+20%">run</prosody></speak>',
        voice_id="en-US-JennyNeural",
        locale="en-US",
    )

    assert (
        '<voice name="en-US-JennyNeural"><prosody rate="-10%" pitch="+8%" volume="+20%">run</prosody></voice>'
        in ssml
    )


def test_build_azure_ssml_escapes_attribute_quotes() -> None:
    from xml.etree import ElementTree

    voice = 'ko-KR-Voice" injected="value'
    ssml = build_azure_ssml(text="학교", locale="ko-KR", voice_id=voice)
    root = ElementTree.fromstring(ssml)
    assert list(root)[0].attrib == {"name": voice}


def test_azure_adapter_preserves_native_word_prosody_at_sdk_boundary(tmp_path: Path) -> None:
    from xml.etree import ElementTree

    adapter = AzureSpeechAdapter(
        Settings(_env_file=None, azure_speech_key="fixture", azure_speech_region="eastus"),
        speechsdk_module=_FAKE_SPEECHSDK,
    )
    adapter.synthesize(
        ssml_text=(
            '<speak xmlns="http://www.w3.org/2001/10/synthesis" version="1.0" '
            'xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural">'
            '<break time="100ms"/><prosody rate="-15%" volume="+10%">'
            '<phoneme alphabet="ipa" ph="ˈka.zɐ">casa</phoneme>'
            '</prosody><break time="250ms"/></voice></speak>'
        ),
        voice_id="pt-BR-FranciscaNeural",
        locale="pt-BR",
        output_path=tmp_path / "word.mp3",
        audio_format="audio-24khz-48kbitrate-mono-mp3",
    )
    root = ElementTree.fromstring(_FakeSpeechSynthesizer.latest_ssml)
    ns = {"s": "http://www.w3.org/2001/10/synthesis"}
    voice = root.find("s:voice", ns)
    assert voice.attrib == {"name": "pt-BR-FranciscaNeural"}
    prosody = voice.find("s:prosody", ns)
    assert prosody is not None
    assert prosody.attrib == {"rate": "-15%", "volume": "+10%"}
    assert prosody.find("s:phoneme", ns).attrib == {"alphabet": "ipa", "ph": "ˈka.zɐ"}
    assert [item.attrib for item in voice.findall("s:break", ns)] == [
        {"time": "100ms"},
        {"time": "250ms"},
    ]
    assert "".join(root.itertext()) == "casa"


@pytest.mark.parametrize(
    "text",
    [
        '<speak xml:lang="fr-FR"><voice name="pt-BR-FranciscaNeural">casa</voice></speak>',
        '<speak xml:lang="pt-BR"><voice name="pt-BR-OtherNeural">casa</voice></speak>',
        '<speak><voice name="pt-BR-FranciscaNeural">casa</voice></speak>',
        '<speak xml:lang="pt-BR">outside<voice name="pt-BR-FranciscaNeural">casa</voice></speak>',
        '<speak xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural">casa</voice>outside</speak>',
        '<speak xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural"><voice name="pt-BR-OtherNeural">casa</voice></voice></speak>',
        '<speak><prosody rate="-15%"><audio src="https://example.invalid/clip.mp3"/></prosody></speak>',
        '<speak><prosody onclick="attack()">casa</prosody></speak>',
        '<speak><prosody xmlns="https://example.invalid">casa</prosody></speak>',
        '<speak><emphasis level="strong">casa</emphasis></speak>',
        '<speak><prosody rate="-15%">casa</speak>',
        '<speak xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural">a & b</voice></speak>',
        '<!DOCTYPE speak [<!ENTITY value "casa">]><speak>&value;</speak>',
        '<?xml version="1.0"?><speak>casa</speak>',
        "<speak><speak>casa</speak></speak>",
        '<speak><break time="1s">casa</break></speak>',
    ],
)
def test_build_azure_ssml_rejects_invalid_spoken_markup_instead_of_stripping(text: str) -> None:
    with pytest.raises(ValueError, match="SSML"):
        build_azure_ssml(text=text, locale="pt-BR", voice_id="pt-BR-FranciscaNeural")


def test_azure_adapter_rejects_voice_mismatch_before_sdk_or_files(tmp_path: Path) -> None:
    def unexpected_sdk(**kwargs):
        pytest.fail("invalid SSML reached SDK initialization")

    adapter = AzureSpeechAdapter(
        Settings(_env_file=None, azure_speech_key="fixture", azure_speech_region="eastus"),
        speechsdk_module=SimpleNamespace(SpeechConfig=unexpected_sdk),
    )
    output = tmp_path / "uncreated" / "word.mp3"
    with pytest.raises(ValueError, match="SSML"):
        adapter.synthesize(
            ssml_text='<speak xml:lang="pt-BR"><voice name="pt-BR-Other">casa</voice></speak>',
            voice_id="pt-BR-FranciscaNeural",
            locale="pt-BR",
            output_path=output,
            audio_format="audio-24khz-48kbitrate-mono-mp3",
        )
    assert not output.parent.exists()


@pytest.mark.parametrize(
    "text,spoken",
    [
        ('Hello & "Azure"', 'Hello & "Azure"'),
        ('<speak>Hello & "Azure"</speak>', 'Hello & "Azure"'),
        ('<speak version="1.0">Hello & "Azure"</speak>', 'Hello & "Azure"'),
        ('<speak>Hello &amp; "Azure"</speak>', 'Hello & "Azure"'),
        ('<speak><prosody rate="-15%">casa &amp; livro</prosody></speak>', "casa & livro"),
        (
            '<speak xml:lang="pt-BR"><voice name="pt-BR-FranciscaNeural">casa &amp; livro</voice></speak>',
            "casa & livro",
        ),
    ],
)
def test_build_azure_ssml_preserves_plain_and_legacy_text_safely(text: str, spoken: str) -> None:
    from xml.etree import ElementTree

    result = build_azure_ssml(text=text, locale="pt-BR", voice_id="pt-BR-FranciscaNeural")
    root = ElementTree.fromstring(result)
    assert "".join(root.itertext()) == spoken
    assert len([node for node in root.iter() if node.tag.endswith("}voice")]) == 1


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
