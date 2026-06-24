"""Google Translate Text to Speech adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.audio_voice_registry import VoiceSelection
from multilang.settings import Settings

_BASE_URL = "https://translate.google.com/translate_tts"
_LANGUAGE_CODES = {
    SupportedLanguage.PT: "pt",
    SupportedLanguage.ES: "es",
    SupportedLanguage.EN: "en",
    SupportedLanguage.FR: "fr",
    SupportedLanguage.DE: "de",
    SupportedLanguage.IT: "it",
    SupportedLanguage.PL: "pl",
    SupportedLanguage.TR: "tr",
    SupportedLanguage.RO: "ro",
    SupportedLanguage.RU: "ru",
    SupportedLanguage.NL: "nl",
    SupportedLanguage.DA: "da",
    SupportedLanguage.NB: "no",
    SupportedLanguage.SV: "sv",
}
_VOICE_REGISTRY_VERSION = "google-translate-tts-v1"


class GoogleTranslateSpeechAdapterError(RuntimeError):
    """Raised when Google Translate TTS cannot synthesize audio."""


class GoogleTranslateSpeechAdapter:
    """Synthesize MP3 audio with Google Translate TTS."""

    provider = AudioProvider.GOOGLE_TRANSLATE
    audio_format = AudioFormat.MP3

    def __init__(self, settings: Settings | None = None, *, urlopen_func: Any = urlopen) -> None:
        self.settings = settings or Settings()
        self._urlopen = urlopen_func

    def available_voice_ids(self) -> set[str] | None:
        return None

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        language_code = _LANGUAGE_CODES[language]
        return VoiceSelection(
            language=language,
            voice_id=language_code,
            locale=language_code,
            registry_version=_VOICE_REGISTRY_VERSION,
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
        if audio_format != AudioFormat.MP3.value:
            raise GoogleTranslateSpeechAdapterError("Google Translate TTS supports mp3 output only")

        language_code = _language_code(voice_id=voice_id, locale=locale)
        plain_text = _extract_plain_text(ssml_text)
        if not plain_text.strip():
            raise GoogleTranslateSpeechAdapterError("Google Translate TTS requires non-empty text")

        request = self._build_request(language_code=language_code, text=plain_text)
        try:
            with self._urlopen(request, timeout=30) as response:
                audio_bytes = response.read()
        except Exception as exc:  # noqa: BLE001 - urllib/provider errors are heterogeneous.
            raise GoogleTranslateSpeechAdapterError("Google Translate TTS request failed") from exc
        if not audio_bytes:
            raise GoogleTranslateSpeechAdapterError("Google Translate TTS returned empty audio")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)
        return AudioSynthesisResponse(
            storage_path=output_path,
            byte_size=len(audio_bytes),
            duration_ms=None,
            provider=self.provider,
            voice_id=voice_id,
            locale=locale,
            audio_format=self.audio_format,
        )

    def _build_request(self, *, language_code: str, text: str) -> Request:
        query = urlencode(
            {
                "ie": "UTF-8",
                "client": "tw-ob",
                "tl": language_code,
                "q": text,
            }
        )
        return Request(
            f"{_BASE_URL}?{query}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "audio/mpeg",
            },
            method="GET",
        )


def _language_code(*, voice_id: str, locale: str) -> str:
    candidate = (voice_id or locale).strip().split("-", maxsplit=1)[0]
    if not candidate:
        raise GoogleTranslateSpeechAdapterError("Google Translate TTS requires a language code")
    return candidate


def _extract_plain_text(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("<"):
        return stripped
    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError:
        return stripped
    return " ".join(part.strip() for part in root.itertext() if part.strip())


__all__ = ["GoogleTranslateSpeechAdapter", "GoogleTranslateSpeechAdapterError"]
