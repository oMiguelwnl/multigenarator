"""Audio adapter that tries configured providers in order."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path

from multilang.domain.audio import AudioFormat, AudioProvider
from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_synthesis import AudioSynthesisAdapter, AudioSynthesisResponse
from multilang.services.audio_voice_registry import VoiceSelection, VoiceSelectionError, select_voice


@dataclass(frozen=True, slots=True)
class _ProviderCandidate:
    adapter: AudioSynthesisAdapter
    selection: VoiceSelection
    provider: AudioProvider
    audio_format: AudioFormat


class FallbackAudioAdapter:
    """Try primary audio synthesis first, then fallback providers per asset."""

    provider = AudioProvider.AZURE
    audio_format = AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3

    def __init__(self, adapters: list[AudioSynthesisAdapter]) -> None:
        if not adapters:
            raise ValueError("at least one audio adapter is required")
        self.adapters = adapters
        self._chains: dict[str, list[_ProviderCandidate]] = {}

    def available_voice_ids(self) -> set[str] | None:
        return None

    def select_voice(self, language: SupportedLanguage) -> VoiceSelection:
        candidates: list[_ProviderCandidate] = []
        for adapter in self.adapters:
            try:
                selection = _select_adapter_voice(adapter, language)
            except Exception:
                continue
            candidates.append(
                _ProviderCandidate(
                    adapter=adapter,
                    selection=selection,
                    provider=_adapter_provider(adapter),
                    audio_format=_adapter_audio_format(adapter),
                )
            )

        if not candidates:
            raise VoiceSelectionError(f"No audio provider voice available for language {language.value}")

        chain_id = _chain_id(language, candidates)
        self._chains[chain_id] = candidates
        first = candidates[0]
        return VoiceSelection(
            language=language,
            voice_id=chain_id,
            locale=first.selection.locale,
            registry_version="fallback-" + "-".join(candidate.provider.value for candidate in candidates),
            fallback_used=first.selection.fallback_used,
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
        candidates = self._chains.get(voice_id)
        if candidates is None:
            raise RuntimeError("unknown audio fallback chain")

        last_error: Exception | None = None
        for index, candidate in enumerate(candidates):
            try:
                response = candidate.adapter.synthesize(
                    ssml_text=ssml_text,
                    voice_id=candidate.selection.voice_id,
                    locale=candidate.selection.locale,
                    output_path=output_path,
                    audio_format=candidate.audio_format.value,
                )
                if response.byte_size <= 0 or not response.storage_path.exists():
                    raise RuntimeError("provider returned empty audio")
                return replace(
                    response,
                    provider=response.provider or candidate.provider,
                    fallback_used=index > 0 or candidate.selection.fallback_used or bool(response.fallback_used),
                )
            except Exception as exc:  # noqa: BLE001 - providers expose heterogeneous exceptions.
                last_error = exc
                continue

        assert last_error is not None
        raise RuntimeError(f"all audio providers failed; last_error={type(last_error).__name__}") from last_error


def _select_adapter_voice(adapter: AudioSynthesisAdapter, language: SupportedLanguage) -> VoiceSelection:
    adapter_selector = getattr(adapter, "select_voice", None)
    if callable(adapter_selector):
        return adapter_selector(language)
    return select_voice(language, available_voice_ids=adapter.available_voice_ids())


def _adapter_provider(adapter: AudioSynthesisAdapter) -> AudioProvider:
    return AudioProvider(getattr(adapter, "provider", AudioProvider.AZURE))


def _adapter_audio_format(adapter: AudioSynthesisAdapter) -> AudioFormat:
    return AudioFormat(getattr(adapter, "audio_format", AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3))


def _chain_id(language: SupportedLanguage, candidates: list[_ProviderCandidate]) -> str:
    raw = "|".join(
        f"{candidate.provider.value}:{candidate.selection.voice_id}:{candidate.audio_format.value}"
        for candidate in candidates
    )
    digest = sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"fallback-{language.value}-{digest}"


__all__ = ["FallbackAudioAdapter"]
