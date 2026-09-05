"""Typed audio contracts for persisted Phase 4 synthesis records."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


def _stable_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class AudioAssetKind(str, Enum):
    WORD = "word"
    SENTENCE = "sentence"


class AudioSynthesisStatus(str, Enum):
    PENDING = "pending"
    SYNTHESIZED = "synthesized"
    FAILED = "failed"


class AudioReviewStatus(str, Enum):
    NOT_REVIEWED = "not_reviewed"
    SYNTHESIZED_PENDING = "synthesized_pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AudioProvider(str, Enum):
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    GOOGLE_TRANSLATE = "google_translate"


class AudioFormat(str, Enum):
    AUDIO_24KHZ_48KBITRATE_MONO_MP3 = "audio-24khz-48kbitrate-mono-mp3"
    MP3_44100_128 = "mp3_44100_128"
    MP3 = "mp3"


class NormalizedTtsInput(BaseModel):
    display_text: str = Field(min_length=1)
    tts_text: str = Field(min_length=1)
    ssml_text: str | None = None
    text_hash: str | None = None
    ssml_hash: str | None = None
    synthesis_request_sha256: str | None = Field(default=None, min_length=64, max_length=64)

    @field_validator("synthesis_request_sha256")
    @classmethod
    def request_hash_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("synthesis_request_sha256 must be lowercase SHA-256")
        return value

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
    provider_sdk_version: str | None = Field(default=None, max_length=64)
    voice_profile_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    catalog_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    synthesis_request_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    artifact_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    audio_review_status: AudioReviewStatus | None = None
    audio_review_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    heard_review_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    fallback_origin: str | None = Field(default=None, max_length=128)
    rejection_reason_code: str | None = Field(default=None, max_length=64)

    @field_validator(
        "voice_profile_sha256",
        "catalog_receipt_sha256",
        "synthesis_request_sha256",
        "artifact_sha256",
        "audio_review_receipt_sha256",
        "heard_review_receipt_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return value
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError(f"{getattr(info, 'field_name', 'hash')} must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def approved_audio_requires_exact_reviews(self) -> Self:
        if self.audio_review_status is not AudioReviewStatus.APPROVED:
            return self
        if self.status is not AudioSynthesisStatus.SYNTHESIZED:
            raise ValueError("approved audio must be synthesized")
        if self.fallback_used:
            raise ValueError("approved Korean audio cannot use fallback")
        required = (
            self.voice_profile_sha256,
            self.catalog_receipt_sha256,
            self.synthesis_request_sha256,
            self.artifact_sha256,
            self.audio_review_receipt_sha256,
            self.heard_review_receipt_sha256,
        )
        if any(value is None for value in required):
            raise ValueError("approved Korean audio requires exact profile, artifact, and review hashes")
        return self


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

    @property
    def ready_for_korean_final_export(self) -> bool:
        return (
            self.provenance.status is AudioSynthesisStatus.SYNTHESIZED
            and self.provenance.audio_review_status is AudioReviewStatus.APPROVED
            and self.provenance.artifact_sha256 is not None
            and self.provenance.audio_review_receipt_sha256 is not None
            and self.provenance.heard_review_receipt_sha256 is not None
            and not self.provenance.fallback_used
        )

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
    "AudioReviewStatus",
    "AudioSynthesisStatus",
    "NormalizedTtsInput",
]
