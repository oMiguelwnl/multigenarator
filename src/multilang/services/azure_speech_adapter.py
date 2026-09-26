"""Azure Speech SDK adapter for shipped audio synthesis."""

from __future__ import annotations

import importlib
import json
import math
import re
from contextlib import suppress
from datetime import timedelta
from pathlib import Path
from threading import Event, Thread
from types import ModuleType
from typing import Any
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.settings import Settings

_VOICE_LIST_PATH = "/cognitiveservices/voices/list"
_LEGACY_TEXT_SPEAK_RE = re.compile(
    r"""^<speak(?:\s+version=(?:"1\.0"|'1\.0'))?\s*>([^<>]*)</speak>$""", re.DOTALL
)
_SSML_NAMESPACE = "http://www.w3.org/2001/10/synthesis"
_XML_LANGUAGE = "{http://www.w3.org/XML/1998/namespace}lang"
_XML_ESCAPES = {'"': "&quot;", "'": "&apos;"}
_SSML_ATTRIBUTES = {
    "speak": {"version", _XML_LANGUAGE},
    "voice": {"name"},
    "prosody": {"rate", "pitch", "volume", "duration"},
    "phoneme": {"alphabet", "ph"},
    "break": {"time", "strength"},
}
_OUTPUT_FORMATS = {
    "audio-24khz-48kbitrate-mono-mp3": "Audio24Khz48KBitRateMonoMp3",
    "pcm_s16le_wav": "Riff24Khz16BitMonoPcm",
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

        payload = self.fetch_voice_inventory()

        self._cached_voice_ids = {
            item["ShortName"]
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("ShortName"), str)
        }
        return set(self._cached_voice_ids)

    def fetch_voice_inventory(self, endpoint_url: str | None = None) -> list[dict[str, Any]]:
        """Fetch Azure voice inventory metadata without synthesizing audio."""

        self._require_credentials()
        request = Request(
            endpoint_url or self._voice_inventory_url,
            headers={
                "Ocp-Apim-Subscription-Key": self.settings.azure_speech_key,
                "Accept": "application/json",
            },
            method="GET",
        )
        with self._urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise AzureSpeechAdapterError("Azure Speech voice inventory payload is invalid")
        return [item for item in payload if isinstance(item, dict)]

    def fetch_voice_inventory_for_locale(
        self, locale: str, *, timeout_seconds: float = 30
    ) -> list[dict[str, str]]:
        """Query one locale through the SDK, with a bounded read-only wait."""
        if (len(locale) > 35 or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})+", locale)
                or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
            raise ValueError("Voice inventory requires a locale and a finite positive timeout")
        self._require_credentials()
        speechsdk = self._speechsdk
        completed = Event()
        results = []

        def query():
            try:
                config = speechsdk.SpeechConfig(
                    subscription=self.settings.azure_speech_key,
                    region=self.settings.azure_speech_region,
                )
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
                results.append(synthesizer.get_voices_async(locale).get())
            except Exception:
                # SDK messages may include provider details; do not expose them.
                pass
            finally:
                completed.set()

        Thread(target=query, daemon=True).start()
        if not completed.wait(timeout_seconds):
            raise TimeoutError("Azure Speech voice inventory timed out")
        if not results or results[0].reason != speechsdk.ResultReason.VoicesListRetrieved:
            raise AzureSpeechAdapterError("Azure Speech voice inventory query failed")
        return [
            {"ShortName": voice.short_name, "Locale": voice.locale}
            for voice in results[0].voices if voice.locale == locale
        ]

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
        timeout_seconds: float | None = None,
    ) -> AudioSynthesisResponse:
        if timeout_seconds is not None and (
            not math.isfinite(timeout_seconds) or timeout_seconds <= 0
        ):
            raise ValueError("Azure synthesis timeout must be finite and positive")
        self._require_credentials()
        ssml = build_azure_ssml(text=ssml_text, locale=locale, voice_id=voice_id)
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

        audio_config = (
            speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            if timeout_seconds is None
            else None
        )
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        if timeout_seconds is None:
            result = synthesizer.speak_ssml_async(ssml).get()
        else:
            completed = Event()
            results = []

            def on_result(event):
                results.append(event.result)
                completed.set()

            synthesizer.synthesis_completed.connect(on_result)
            synthesizer.synthesis_canceled.connect(on_result)
            try:
                future = synthesizer.speak_ssml_async(ssml)
                if not completed.wait(timeout_seconds):
                    # Never wait indefinitely on either SDK future. Timeout is an
                    # ambiguous provider outcome, so callers must not auto-retry it.
                    with suppress(Exception):
                        synthesizer.stop_speaking_async()
                    raise TimeoutError("Azure Speech synthesis timed out")
                result = results[0]
                del future
            finally:
                # Cleanup must not replace an unknown provider outcome with a
                # local SDK error, or discard an already completed result.
                for signal in (synthesizer.synthesis_completed, synthesizer.synthesis_canceled):
                    with suppress(Exception):
                        signal.disconnect(on_result)
        completed_reason = getattr(speechsdk.ResultReason, "SynthesizingAudioCompleted", None)
        if getattr(result, "reason", None) != completed_reason:
            raise AzureSpeechAdapterError(self._build_cancellation_message(result))

        byte_size = len(getattr(result, "audio_data", b""))
        if timeout_seconds is not None:
            output_path.write_bytes(getattr(result, "audio_data", b""))
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
        cancellation = getattr(result, "cancellation_details", None)
        if cancellation is None:
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

    safe_ssml = _extract_safe_spoken_ssml(text, locale=locale, voice_id=voice_id)
    if safe_ssml is None:
        safe_ssml = escape(text.strip(), _XML_ESCAPES)
    attributes = {'"': "&quot;", "'": "&apos;"}
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{escape(locale, attributes)}">'
        f'<voice name="{escape(voice_id, attributes)}">{safe_ssml}</voice>'
        "</speak>"
    )


def _extract_safe_spoken_ssml(text: str, *, locale: str, voice_id: str) -> str | None:
    """Preserve bounded pronunciation markup and reject mismatched native controls."""
    stripped = text.strip()
    if not stripped:
        return ""
    if "<!" in stripped or "<?" in stripped:
        raise ValueError("SSML declarations and entities are prohibited")
    if stripped.startswith("<") and len(stripped.encode("utf-8")) > 64000:
        raise ValueError("SSML exceeds the byte limit")

    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError as exc:
        # Old callers wrapped literal text without XML-escaping ampersands. This
        # narrowly scoped compatibility case cannot contain pronunciation markup.
        legacy = _LEGACY_TEXT_SPEAK_RE.fullmatch(stripped)
        if legacy is not None:
            return escape(legacy.group(1).strip(), _XML_ESCAPES)
        if re.match(r"<\s*[a-zA-Z_!?]", stripped):
            raise ValueError("SSML must be well formed") from exc
        return None

    elements = list(root.iter())
    names = [element.tag.rsplit("}", 1)[-1] for element in elements]
    if len(elements) > 256 or names[0] != "speak" or names.count("speak") != 1:
        raise ValueError("SSML structure limit or root mismatch")
    for element, name in zip(elements, names, strict=True):
        if name not in _SSML_ATTRIBUTES or set(element.attrib) - _SSML_ATTRIBUTES[name]:
            raise ValueError("SSML contains unapproved elements or attributes")
        if element.tag.startswith("{") and not element.tag.startswith(f"{{{_SSML_NAMESPACE}}}"):
            raise ValueError("SSML contains an unapproved namespace")
        if name in {"break", "phoneme"} and list(element):
            raise ValueError("SSML pronunciation leaf cannot contain nested markup")
        if name == "break" and (element.text or "").strip():
            raise ValueError("SSML break cannot contain spoken text")
    if root.get("version") not in {None, "1.0"}:
        raise ValueError("SSML version is unsupported")
    if root.get(_XML_LANGUAGE) not in {None, locale}:
        raise ValueError("SSML locale differs from the requested locale")
    if "voice" in names:
        children = list(root)
        if (
            root.get(_XML_LANGUAGE) != locale
            or names.count("voice") != 1
            or len(children) != 1
            or children[0].tag.rsplit("}", 1)[-1] != "voice"
            or (root.text or "").strip()
            or (children[0].tail or "").strip()
        ):
            raise ValueError("SSML requires one explicit voice and locale enclosing all text")
        voice = children[0]
        if voice.get("name") != voice_id:
            raise ValueError("SSML voice differs from the requested voice")
        return _spoken_markup(voice)
    return _spoken_markup(root)


def _spoken_markup(container: ElementTree.Element) -> str:
    """Serialize only a previously validated tree into the selected Azure voice."""
    parts = [escape(container.text or "", _XML_ESCAPES)]
    for child in container:
        name = child.tag.rsplit("}", 1)[-1]
        attributes = "".join(
            f' {key}="{escape(value, _XML_ESCAPES)}"' for key, value in child.attrib.items()
        )
        parts.append(f"<{name}{attributes}>{_spoken_markup(child)}</{name}>")
        parts.append(escape(child.tail or "", _XML_ESCAPES))
    return "".join(parts)


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
