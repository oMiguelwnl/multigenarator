"""Azure Speech SDK adapter for shipped audio synthesis."""

from __future__ import annotations

from datetime import timedelta
import importlib
import json
from pathlib import Path
import re
from types import ModuleType
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from urllib.request import Request, urlopen

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.settings import Settings

_VOICE_LIST_PATH = "/cognitiveservices/voices/list"
_LEGACY_SPEAK_RE = re.compile(r"^<speak(?:\s[^>]*)?>(.*)</speak>$", re.DOTALL)
_OUTPUT_FORMATS = {
    "audio-24khz-48kbitrate-mono-mp3": "Audio24Khz48KBitRateMonoMp3",
}


class AzureSpeechAdapterError(RuntimeError):
    """Raised when Azure Speech cannot synthesize playable media."""


class AzureSpeechAdapter:
    """Resolve Azure voice inventory and synthesize SSML to files."""

    provider = AudioProvider.AZURE
    audio_format = AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        speechsdk_module: ModuleType | None = None,
        urlopen_func: Any = urlopen,
    ) -> None:
        self.settings = settings or Settings()
        self._speechsdk_module = speechsdk_module
        self._urlopen = urlopen_func
        self._cached_voice_ids: set[str] | None = None

    def available_voice_ids(self) -> set[str] | None:
        if self._cached_voice_ids is not None:
            return set(self._cached_voice_ids)
        if not self.settings.azure_speech_key or not self.settings.azure_speech_region:
            return set()

        request = Request(
            self._voice_inventory_url,
            headers={
                "Ocp-Apim-Subscription-Key": self.settings.azure_speech_key,
                "Accept": "application/json",
            },
            method="GET",
        )
        with self._urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self._cached_voice_ids = {
            item["ShortName"]
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("ShortName"), str)
        }
        return set(self._cached_voice_ids)

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        self._require_credentials()
        speechsdk = self._speechsdk
        output_path.parent.mkdir(parents=True, exist_ok=True)

        speech_config = speechsdk.SpeechConfig(
            subscription=self.settings.azure_speech_key,
            region=self.settings.azure_speech_region,
        )
        speech_config.speech_synthesis_language = locale
        speech_config.speech_synthesis_voice_name = voice_id
        speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, _OUTPUT_FORMATS[audio_format])
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        result = synthesizer.speak_ssml_async(
            build_azure_ssml(text=ssml_text, locale=locale, voice_id=voice_id)
        ).get()
        completed_reason = getattr(speechsdk.ResultReason, "SynthesizingAudioCompleted", None)
        if getattr(result, "reason", None) != completed_reason:
            raise AzureSpeechAdapterError(self._build_cancellation_message(result))

        byte_size = len(getattr(result, "audio_data", b""))
        if byte_size == 0 and output_path.exists():
            byte_size = output_path.stat().st_size
        return AudioSynthesisResponse(
            storage_path=output_path,
            byte_size=byte_size,
            duration_ms=_duration_to_ms(getattr(result, "audio_duration", None)),
        )

    @property
    def _speechsdk(self) -> ModuleType:
        if self._speechsdk_module is None:
            self._speechsdk_module = importlib.import_module("azure.cognitiveservices.speech")
        return self._speechsdk_module

    @property
    def _voice_inventory_url(self) -> str:
        return f"https://{self.settings.azure_speech_region}.tts.speech.microsoft.com{_VOICE_LIST_PATH}"

    def _require_credentials(self) -> None:
        if not self.settings.azure_speech_key or not self.settings.azure_speech_region:
            raise AzureSpeechAdapterError(
                "Azure Speech credentials are required: set MULTILANG_AZURE_SPEECH_KEY and MULTILANG_AZURE_SPEECH_REGION"
            )

    def _build_cancellation_message(self, result: object) -> str:
        details = getattr(self._speechsdk, "CancellationDetails", None)
        from_result = getattr(details, "from_result", None)
        if not callable(from_result):
            return "Azure Speech synthesis failed"

        cancellation = from_result(result)
        parts = ["Azure Speech synthesis failed"]

        reason = getattr(cancellation, "reason", None)
        if reason is not None:
            parts.append(f"reason={reason}")

        error_code = getattr(cancellation, "error_code", None)
        if error_code is not None:
            parts.append(f"error_code={error_code}")

        error_details = getattr(cancellation, "error_details", None)
        if error_details:
            parts.append(f"details={error_details}")

        return "; ".join(parts)


def build_azure_ssml(*, text: str, locale: str, voice_id: str) -> str:
    """Normalize plain text or legacy SSML into Azure-compatible SSML."""

    safe_ssml = _extract_safe_spoken_ssml(text)
    if safe_ssml is None:
        plain_text = _extract_spoken_text(text)
        safe_ssml = escape(plain_text, {'"': '&quot;', "'": '&apos;'})
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{escape(locale)}">'
        f'<voice name="{escape(voice_id)}">{safe_ssml}</voice>'
        "</speak>"
    )


def _extract_safe_spoken_ssml(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return ""

    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError:
        return None

    tag_name = root.tag.rsplit("}", 1)[-1]
    if tag_name != "speak":
        return None

    safe_children: list[str] = []
    if root.text and root.text.strip():
        return None
    for child in list(root):
        child_tag = child.tag.rsplit("}", 1)[-1]
        if child_tag != "prosody":
            return None
        safe_children.append(ElementTree.tostring(child, encoding="unicode", short_empty_elements=False))
        if child.tail and child.tail.strip():
            return None
    return "".join(safe_children)


def _extract_spoken_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError:
        legacy_match = _LEGACY_SPEAK_RE.match(stripped)
        if legacy_match is not None:
            return legacy_match.group(1).strip()
        return stripped

    tag_name = root.tag.rsplit("}", 1)[-1]
    if tag_name != "speak":
        return "".join(root.itertext()).strip() or stripped

    return "".join(root.itertext()).strip()


def _duration_to_ms(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, timedelta):
        return int(value.total_seconds() * 1000)
    if isinstance(value, int):
        return value
    total_seconds = getattr(value, "total_seconds", None)
    if callable(total_seconds):
        return int(total_seconds() * 1000)
    return None


__all__ = ["AzureSpeechAdapter", "AzureSpeechAdapterError"]
