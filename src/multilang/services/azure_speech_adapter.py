"""Azure Speech SDK adapter for shipped audio synthesis."""

from __future__ import annotations

from datetime import timedelta
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.request import Request, urlopen

from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.settings import Settings

_VOICE_LIST_PATH = "/cognitiveservices/voices/list"
_OUTPUT_FORMATS = {
    "audio-24khz-48kbitrate-mono-mp3": "Audio24Khz48KBitRateMonoMp3",
}


class AzureSpeechAdapterError(RuntimeError):
    """Raised when Azure Speech cannot synthesize playable media."""


class AzureSpeechAdapter:
    """Resolve Azure voice inventory and synthesize SSML to files."""

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
        result = synthesizer.speak_ssml_async(ssml_text).get()
        completed_reason = getattr(speechsdk.ResultReason, "SynthesizingAudioCompleted", None)
        if getattr(result, "reason", None) != completed_reason:
            details = speechsdk.CancellationDetails.from_result(result)
            raise AzureSpeechAdapterError(
                f"Azure Speech synthesis failed: {getattr(details, 'reason', 'unknown')}"
            )

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
