"""Typed audio contracts for persisted Phase 4 synthesis records."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256

from pydantic import BaseModel, Field, model_validator


def _stable_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class AudioAssetKind(str, Enum):
    WORD = "word"
    SENTENCE = "sentence"


class AudioSynthesisStatus(str, Enum):
    PENDING = "pending"
    SYNTHESIZED = "synthesized"
    FAILED = "failed"


class AudioProvider(str, Enum):
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"


class AudioFormat(str, Enum):
    AUDIO_24KHZ_48KBITRATE_MONO_MP3 = "audio-24khz-48kbitrate-mono-mp3"
    MP3_44100_128 = "mp3_44100_128"


class NormalizedTtsInput(BaseModel):
    display_text: str = Field(min_length=1)
    tts_text: str = Field(min_length=1)
    ssml_text: str | None = None
    text_hash: str | None = None
    ssml_hash: str | None = None

    @model_validator(mode="after")
    def populate_hashes(self) -> "NormalizedTtsInput":
        if self.text_hash is None:
            self.text_hash = _stable_hash(self.tts_text)
        if self.ssml_hash is None:
            self.ssml_hash = _stable_hash(self.ssml_text or self.tts_text)
        return self


class AudioProvenance(BaseModel):
    provider: AudioProvider
    voice_id: str = Field(min_length=1)
    locale: str = Field(min_length=1)
    format: AudioFormat
    text_hash: str = Field(min_length=1)
    ssml_hash: str = Field(min_length=1)
    storage_path: str = Field(min_length=1)
    byte_size: int = Field(ge=0)
    duration_ms: int | None = Field(default=None, ge=0)
    status: AudioSynthesisStatus
    fallback_used: bool = False


class AudioAssetRecord(BaseModel):
    job_id: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    asset_kind: AudioAssetKind
    display_text: str = Field(min_length=1)
    normalized_input: NormalizedTtsInput
    provenance: AudioProvenance

    @property
    def identity_key(self) -> tuple[str, str, AudioAssetKind]:
        return (self.job_id, self.item_key, self.asset_kind)

    @model_validator(mode="after")
    def align_display_text(self) -> "AudioAssetRecord":
        if self.normalized_input.display_text != self.display_text:
            raise ValueError("display_text must match normalized_input.display_text")
        return self


__all__ = [
    "AudioAssetKind",
    "AudioAssetRecord",
    "AudioFormat",
    "AudioProvenance",
    "AudioProvider",
    "AudioSynthesisStatus",
    "NormalizedTtsInput",
]
