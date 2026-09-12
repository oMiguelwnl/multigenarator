"""Context-complete pronunciation identity and immutable audio versions."""

from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.audio import AudioAssetKind, AudioFormat, AudioProvider
from multilang.domain.content import canonical_content_hash


class PronunciationSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"] = "1"
    language: str = Field(min_length=2, max_length=8)
    language_profile_version: str = Field(min_length=1, max_length=128)
    display_text: str = Field(min_length=1, max_length=4000)
    normalized_text: str = Field(min_length=1, max_length=4000)
    contextual_reading: str = Field(min_length=1, max_length=4000)
    context: str = Field(min_length=1, max_length=4000)
    sense_id: str = Field(min_length=1, max_length=255)
    morphological_analysis_id: str | None = Field(
        default=None, min_length=1, max_length=255
    )
    locale: str = Field(min_length=1, max_length=64)
    voice_id: str = Field(min_length=1, max_length=255)
    ssml: str = Field(min_length=1, max_length=16000)
    pronunciation_policy_version: str = Field(min_length=1, max_length=128)
    provider: AudioProvider
    provider_model_version: str = Field(min_length=1, max_length=255)
    audio_format: AudioFormat
    asset_kind: AudioAssetKind

    @model_validator(mode="after")
    def exact_normalization(self) -> PronunciationSignature:
        if unicodedata.normalize("NFC", self.display_text) != self.normalized_text:
            raise ValueError(
                "normalized pronunciation text must be exact NFC displayed text"
            )
        if self.locale.split("-", 1)[0] != self.language:
            raise ValueError("pronunciation locale must belong to its language")
        return self

    @property
    def signature_sha256(self) -> str:
        return canonical_content_hash(self.model_dump(mode="json"))


class AudioVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    signature: PronunciationSignature
    storage_path: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)
    namespace: str = Field(default="core", min_length=1)
    license_receipt_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    review_receipt_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def approval_evidence(self) -> AudioVersion:
        if self.review_status == "approved" and (
            not self.review_receipt_sha256 or not self.license_receipt_sha256
        ):
            raise ValueError("approved audio requires review and license evidence")
        if self.namespace != "core" and (
            not self.namespace.startswith("user:") or len(self.namespace) <= 5
        ):
            raise ValueError(
                "audio namespace must be core or an explicit user namespace"
            )
        return self

    @property
    def version_id(self) -> str:
        return "audio:1:" + canonical_content_hash(
            {
                "signature": self.signature.signature_sha256,
                "artifact": self.artifact_sha256,
                "bytes": self.byte_size,
                "namespace": self.namespace,
                "review_status": self.review_status,
                "review_receipt": self.review_receipt_sha256,
                "license_receipt": self.license_receipt_sha256,
            }
        )


AudioContract = AudioVersion
