"""Latin MVP audio metadata contracts and export-readiness validators."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


LatinAudioKind = Literal["word", "sentence"]
LatinAudioProvider = Literal["espeak-ng", "azure-multilingual-experimental"]
LatinAudioReviewStatus = Literal["needs_playback_review", "approved", "rejected", "blocked"]


def normalize_latin_audio_text(value: str) -> str:
    """Normalize generated Latin audio text for exact hash and source-pack comparison."""

    return " ".join(value.split())


def latin_audio_text_hash(value: str) -> str:
    """Return the SHA-256 hash used for auditable Latin audio generated text."""

    return sha256(normalize_latin_audio_text(value).encode("utf-8")).hexdigest()


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("required text field must not be blank")
    return stripped


def _strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _not_blank(value)


class LatinAudioArtifact(BaseModel):
    """One auditable Latin word or sentence audio artifact."""

    audio_kind: LatinAudioKind
    provider: LatinAudioProvider
    provider_version: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    pronunciation_policy: str = Field(min_length=1)
    generated_text: str = Field(min_length=1)
    text_hash: str = Field(min_length=64, max_length=64)
    playback_review_status: LatinAudioReviewStatus
    storage_path: str = Field(min_length=1)
    fallback_reason: str | None = None

    _strip_text = field_validator(
        "provider_version",
        "voice",
        "pronunciation_policy",
        "generated_text",
        "storage_path",
    )(_not_blank)
    _strip_optional_text_fields = field_validator("fallback_reason")(_strip_optional_text)

    @field_validator("generated_text")
    @classmethod
    def normalize_generated_text(cls, value: str) -> str:
        return normalize_latin_audio_text(value)

    @model_validator(mode="after")
    def validate_hash_and_fallback_reason(self) -> "LatinAudioArtifact":
        if self.text_hash != latin_audio_text_hash(self.generated_text):
            raise ValueError("text_hash must match normalized generated_text")
        if self.provider != "espeak-ng" and self.fallback_reason is None:
            raise ValueError("fallback_reason is required for fallback or experimental providers")
        if self.playback_review_status == "blocked" and self.fallback_reason is None:
            raise ValueError("fallback_reason is required for blocked audio records")
        return self


class LatinAudioPair(BaseModel):
    """Word and sentence audio artifacts for one Latin MVP source-pack item."""

    item_key: str = Field(min_length=1)
    word: LatinAudioArtifact | None = None
    sentence: LatinAudioArtifact | None = None

    _strip_text = field_validator("item_key")(_not_blank)

    @model_validator(mode="after")
    def validate_artifact_kinds(self) -> "LatinAudioPair":
        if self.word is not None and self.word.audio_kind != "word":
            raise ValueError("word artifact audio_kind must be word")
        if self.sentence is not None and self.sentence.audio_kind != "sentence":
            raise ValueError("sentence artifact audio_kind must be sentence")
        return self


class LatinAudioManifest(BaseModel):
    """Validated Latin MVP audio manifest with one pair per source-pack item."""

    source_pack_version: Literal["latin-mvp-50-v1"] = "latin-mvp-50-v1"
    artifacts: list[LatinAudioPair]


class LatinAudioSummary(BaseModel):
    """Aggregate Latin audio readiness counts."""

    total_items: int
    approved_items: int
    blocked_items: int
    status_counts: dict[str, dict[str, int]]
    blocking_audio_by_item_key: dict[str, list[str]]


__all__ = [
    "LatinAudioArtifact",
    "LatinAudioKind",
    "LatinAudioManifest",
    "LatinAudioPair",
    "LatinAudioProvider",
    "LatinAudioReviewStatus",
    "LatinAudioSummary",
    "latin_audio_text_hash",
    "normalize_latin_audio_text",
]
