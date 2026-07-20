"""ElevenLabs Text to Speech adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.audio_voice_registry import VoiceSelection
from multilang.settings import Settings

_BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
_LANGUAGE_LOCALES = {
    SupportedLanguage.PT: "pt-BR",
    SupportedLanguage.ES: "es-ES",
    SupportedLanguage.EN: "en-US",
    SupportedLanguage.FR: "fr-FR",
    SupportedLanguage.DE: "de-DE",
    SupportedLanguage.EL: "el-GR",
    SupportedLanguage.IT: "it-IT",
    SupportedLanguage.PL: "pl-PL",
    SupportedLanguage.TR: "tr-TR",
    SupportedLanguage.RO: "ro-RO",
    SupportedLanguage.RU: "ru-RU",
    SupportedLanguage.NL: "nl-NL",
    SupportedLanguage.DA: "da-DK",
    SupportedLanguage.NB: "nb-NO",
    SupportedLanguage.SV: "sv-SE",
    SupportedLanguage.FI: "fi-FI",
    SupportedLanguage.HU: "hu-HU",
    SupportedLanguage.CS: "cs-CZ",
    SupportedLanguage.HR: "hr-HR",
    SupportedLanguage.JA: "ja-JP",
}
_VOICE_REGISTRY_VERSION = "elevenlabs-premade-v1"
_VOICE_BY_LANGUAGE = {
    # ElevenLabs multilingual voices are not language-locked. These defaults
    # favor clear, neutral premade voices for learner audio.
    SupportedLanguage.PT: "EXAVITQu4vr4xnSDxMaL",  # Bella
    SupportedLanguage.ES: "ErXwobaYiN019PkySvjV",  # Antoni
    SupportedLanguage.EN: "21m00Tcm4TlvDq8ikWAM",  # Rachel
    SupportedLanguage.FR: "MF3mGyEYCl7XYWbV9V6O",  # Elli
    SupportedLanguage.DE: "VR6AewLTigWG4xSOukaG",  # Arnold
    SupportedLanguage.EL: "MF3mGyEYCl7XYWbV9V6O",  # Elli
    SupportedLanguage.IT: "AZnzlk1XvdvUeBnXmlld",  # Domi
    SupportedLanguage.PL: "ErXwobaYiN019PkySvjV",  # Antoni
    SupportedLanguage.TR: "pNInz6obpgDQGcFmaJgB",  # Adam
    SupportedLanguage.RO: "EXAVITQu4vr4xnSDxMaL",  # Bella
    SupportedLanguage.RU: "VR6AewLTigWG4xSOukaG",  # Arnold
    SupportedLanguage.NL: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.DA: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.NB: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.SV: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.FI: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.HU: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.CS: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.HR: "TxGEqnHWrfWFTfGW9XjX",  # Josh
    SupportedLanguage.JA: "EXAVITQu4vr4xnSDxMaL",  # Bella
}


class ElevenLabsSpeechAdapterError(RuntimeError):
    """Raised when ElevenLabs cannot synthesize audio."""


class ElevenLabsSpeechAdapter:
    """Synthesize MP3 audio with ElevenLabs multilingual TTS."""

    provider = AudioProvider.ELEVENLABS
    audio_format = AudioFormat.MP3_44100_128

    def __init__(self, settings: Settings | None = None, *, urlopen_func: Any = urlopen) -> None:
        self.settings = settings or Settings()
        self._urlopen = urlopen_func
        self._active_key_index = 0
        self._failed_key_indices: set[int] = set()

    def available_voice_ids(self) -> set[str] | None:
        return None

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        return VoiceSelection(
            language=language,
            voice_id=self.settings.elevenlabs_voice_id or _VOICE_BY_LANGUAGE[language],
            locale=_LANGUAGE_LOCALES[language],
            registry_version=f"{_VOICE_REGISTRY_VERSION}-{self.settings.elevenlabs_model_id}",
            fallback_used=False,
        )

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        self._require_credentials(voice_id)
        resolved_voice_id = self.settings.elevenlabs_voice_id or voice_id
        plain_text = _extract_plain_text(ssml_text)
        if not plain_text.strip():
            raise ElevenLabsSpeechAdapterError("ElevenLabs synthesis requires non-empty text")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        last_error: BaseException | None = None
        for key_index, api_key in self._ordered_api_keys():
            try:
                request = self._build_request(
                    voice_id=resolved_voice_id,
                    text=plain_text,
                    api_key=api_key,
                )
                with self._urlopen(request, timeout=30) as response:
                    audio_bytes = response.read()
                if not audio_bytes:
                    raise ElevenLabsSpeechAdapterError("ElevenLabs returned empty audio")
                self._active_key_index = key_index
                break
            except Exception as exc:  # noqa: BLE001 - API clients expose heterogeneous transient errors.
                last_error = exc
                self._failed_key_indices.add(key_index)
                self._active_key_index = key_index + 1
        else:
            raise ElevenLabsSpeechAdapterError(
                "ElevenLabs synthesis failed for all configured API keys"
            ) from last_error

        output_path.write_bytes(audio_bytes)
        return AudioSynthesisResponse(
            storage_path=output_path,
            byte_size=len(audio_bytes),
            duration_ms=None,
        )

    def _require_credentials(self, voice_id: str) -> None:
        if not self._api_keys():
            raise ElevenLabsSpeechAdapterError(
                "ElevenLabs API key is required: set MULTILANG_ELEVENLABS_API_KEY"
            )

    def _build_request(self, *, voice_id: str, text: str, api_key: str) -> Request:
        return Request(
            self._synthesis_url(voice_id),
            data=json.dumps(
                {
                    "text": text,
                    "model_id": self.settings.elevenlabs_model_id,
                }
            ).encode("utf-8"),
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            },
            method="POST",
        )

    def _ordered_api_keys(self) -> list[tuple[int, str]]:
        keys = self._api_keys()
        start = min(self._active_key_index, len(keys))
        return [(index, keys[index]) for index in range(start, len(keys)) if index not in self._failed_key_indices]

    def _api_keys(self) -> list[str]:
        candidates = [
            self.settings.elevenlabs_api_key,
            self.settings.elevenlabs_api_key_2,
            self.settings.elevenlabs_api_key_3,
            self.settings.elevenlabs_api_key_4,
            *self.settings.elevenlabs_api_keys,
        ]
        keys: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            cleaned = str(candidate or "").strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            keys.append(cleaned)
        return keys

    def _synthesis_url(self, voice_id: str) -> str:
        return (
            f"{_BASE_URL}/{quote(voice_id, safe='')}"
            f"?output_format={quote(self.settings.elevenlabs_output_format, safe='')}"
        )


def _extract_plain_text(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("<"):
        return stripped
    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError:
        return stripped
    return " ".join(part.strip() for part in root.itertext() if part.strip())


__all__ = ["ElevenLabsSpeechAdapter", "ElevenLabsSpeechAdapterError"]
