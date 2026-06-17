"""Latin MVP audio generation fallback orchestration."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, Field

from multilang.services.latin_audio import (
    CURRENT_LATIN_AUDIO_PROVIDER,
    LATIN_FALLBACK_AUDIO_PROVIDERS,
    LatinAudioArtifact,
    LatinAudioKind,
    latin_audio_text_hash,
)


class LatinAudioGenerationResult(BaseModel):
    """Raw provider result before manifest metadata is assembled."""

    provider: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    pronunciation_policy: str = Field(min_length=1)
    storage_path: str = Field(min_length=1)
    fallback_reason: str | None = None


LatinAudioProviderAdapter = Callable[[str, LatinAudioKind, Path], LatinAudioGenerationResult | dict[str, object]]


class LatinAudioGenerationService:
    """Try Google TTS first, then ElevenLabs Italian, then Azure Italian."""

    provider_order = (CURRENT_LATIN_AUDIO_PROVIDER, *LATIN_FALLBACK_AUDIO_PROVIDERS)

    def __init__(self, adapters: dict[str, LatinAudioProviderAdapter]) -> None:
        self.adapters = adapters

    def synthesize(self, text: str, audio_kind: LatinAudioKind, output_path: Path) -> LatinAudioArtifact:
        failures: list[str] = []
        for provider in self.provider_order:
            adapter = self.adapters.get(provider)
            if adapter is None:
                failures.append(provider)
                continue
            try:
                result = LatinAudioGenerationResult.model_validate(adapter(text, audio_kind, output_path))
            except Exception:
                failures.append(provider)
                continue
            fallback_reason = result.fallback_reason
            if provider != CURRENT_LATIN_AUDIO_PROVIDER and fallback_reason is None:
                fallback_reason = f"Fallback after unavailable providers: {', '.join(failures)}."
            return LatinAudioArtifact(
                audio_kind=audio_kind,
                provider=result.provider,
                provider_version=result.provider_version,
                voice=result.voice,
                pronunciation_policy=result.pronunciation_policy,
                generated_text=text,
                text_hash=latin_audio_text_hash(text),
                playback_review_status="approved",
                storage_path=result.storage_path,
                fallback_reason=fallback_reason,
            )
        raise ValueError("no Latin audio provider succeeded")


__all__ = [
    "LatinAudioGenerationResult",
    "LatinAudioGenerationService",
]
