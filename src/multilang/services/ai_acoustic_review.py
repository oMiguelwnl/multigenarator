"""Fail-closed AI acoustic review contracts for Phase 31 media evidence."""

from __future__ import annotations

from datetime import datetime
from copy import deepcopy
from hashlib import sha256
import json
from typing import Final, Literal, Self
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_MAX_IDENTIFIER_LENGTH: Final = 160
_MAX_RELPATH_LENGTH: Final = 512


def ai_acoustic_review_sha256(value: object) -> str:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    elif isinstance(value, dict):
        payload = deepcopy(value)
    else:
        payload = value
    if isinstance(payload, dict):
        payload.pop("content_hash", None)
        payload.pop("canonical_content_hash", None)
        payload.pop("aggregate_root", None)
        for run in payload.get("validator_runs", ()) or ():
            if isinstance(run, dict):
                run.pop("content_hash", None)
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


class _FrozenAcousticModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _identifier(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > _MAX_IDENTIFIER_LENGTH
    ):
        raise ValueError(f"{field_name} must be bounded")
    return value


def _utc(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("timestamp must be exact UTC") from exc
    return value


class AcousticValidatorRun(_FrozenAcousticModel):
    validator_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    validator_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    result: Literal["passed", "blocked", "failed"]
    subject_sha256: str = Field(min_length=64, max_length=64)
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("validator_id", "validator_version")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "validator"))

    @field_validator("subject_sha256", "content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def content_hash_must_bind_run(self) -> Self:
        if self.content_hash != ai_acoustic_review_sha256(self):
            raise ValueError("validator content hash does not match")
        return self


class AIAcousticReviewDecision(_FrozenAcousticModel):
    schema_version: Literal[1]
    policy_id: Literal["phase31-ai-acoustic-review"]
    policy_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    policy_sha256: str = Field(min_length=64, max_length=64)
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    route: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    provider_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    provider_api_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    model_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    model_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    prompt_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    prompt_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    prompt_template_sha256: str = Field(min_length=64, max_length=64)
    output_schema_id: Literal["phase31-ai-acoustic-review-decision"]
    output_schema_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    output_schema_sha256: str = Field(min_length=64, max_length=64)
    source_content_sha256: str = Field(min_length=64, max_length=64)
    candidate_content_sha256: str = Field(min_length=64, max_length=64)
    analyzer_content_sha256: str = Field(min_length=64, max_length=64)
    curriculum_content_sha256: str = Field(min_length=64, max_length=64)
    media_manifest_sha256: str = Field(min_length=64, max_length=64)
    validator_runs: tuple[AcousticValidatorRun, ...] = Field(min_length=1)
    atomic_gate_verdict: Literal["passed", "blocked", "failed"]
    final_consensus_status: Literal["passing", "blocked"]
    reason_codes: tuple[str, ...]
    uncertainty_codes: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)
    pass_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    independence_scope: Literal["fresh-context-no-tools"]
    orchestration_started_at: str = Field(min_length=20, max_length=20)
    orchestration_completed_at: str = Field(min_length=20, max_length=20)
    slot_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    display_text_nfc: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    spoken_text_nfc: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    text_sha256: str = Field(min_length=64, max_length=64)
    synthesis_request_sha256: str = Field(min_length=64, max_length=64)
    synthesis_provider_id: Literal["azure-speech-service"]
    synthesis_provider_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    voice_profile_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    voice_profile_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    locale: Literal["ko-KR"]
    ssml_sha256: str = Field(min_length=64, max_length=64)
    prosody_sha256: str = Field(min_length=64, max_length=64)
    output_format: Literal["pcm_s16le_wav"]
    duration_ms: int = Field(gt=0, le=30_000)
    repository_relpath: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    artifact_sha256: str = Field(min_length=64, max_length=64)
    reviewed_artifact_sha256: str = Field(min_length=64, max_length=64)
    actual_byte_sha256: str = Field(min_length=64, max_length=64)
    canonical_content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "policy_version",
        "route",
        "provider_id",
        "provider_api_version",
        "model_id",
        "model_version",
        "prompt_id",
        "prompt_version",
        "output_schema_version",
        "pass_id",
        "slot_id",
        "voice_profile_id",
        "voice_profile_version",
    )
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "identifier"))

    @field_validator("display_text_nfc", "spoken_text_nfc")
    @classmethod
    def text_must_be_nfc(cls, value: str) -> str:
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("text must be NFC")
        return value

    @field_validator("repository_relpath")
    @classmethod
    def repository_relpath_must_be_safe(cls, value: str) -> str:
        if value.startswith(("/", "~")) or ".." in value.split("/") or "\\" in value:
            raise ValueError("repository relpath must be safe")
        return value

    @field_validator(
        "policy_sha256",
        "prompt_template_sha256",
        "output_schema_sha256",
        "source_content_sha256",
        "candidate_content_sha256",
        "analyzer_content_sha256",
        "curriculum_content_sha256",
        "media_manifest_sha256",
        "text_sha256",
        "synthesis_request_sha256",
        "ssml_sha256",
        "prosody_sha256",
        "artifact_sha256",
        "reviewed_artifact_sha256",
        "actual_byte_sha256",
        "canonical_content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("orchestration_started_at", "orchestration_completed_at")
    @classmethod
    def timestamps_must_be_utc(cls, value: str) -> str:
        return _utc(value)

    @model_validator(mode="after")
    def hashes_and_verdict_must_be_consistent(self) -> Self:
        if not (
            self.artifact_sha256
            == self.reviewed_artifact_sha256
            == self.actual_byte_sha256
        ):
            raise ValueError("audio artifact hashes must match exact bytes")
        if self.atomic_gate_verdict != "passed" or self.final_consensus_status != "passing":
            raise ValueError("decision records only passing acoustic consensus")
        if self.reason_codes or self.uncertainty_codes:
            raise ValueError("passing acoustic decisions cannot carry blockers")
        if any(run.result != "passed" for run in self.validator_runs):
            raise ValueError("passing acoustic decisions require passing validators")
        if self.canonical_content_hash != ai_acoustic_review_sha256(self):
            raise ValueError("canonical content hash does not match")
        return self


class AIAcousticBlocker(_FrozenAcousticModel):
    slot_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    media_kind: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    reason_code: Literal[
        "azure_speech_credentials_missing",
        "provider_execution_not_available",
        "provider_attempt_ceiling_exceeded",
        "provider_execution_failed",
        "acoustic_review_missing",
    ]


class AIAcousticReviewAggregate(_FrozenAcousticModel):
    schema_version: Literal[1]
    phase: Literal["31-hangul-and-pronunciation-i-plus-1"]
    status: Literal["passing", "blocked"]
    media_rights_sha256: str = Field(min_length=64, max_length=64)
    media_authority_sha256: str = Field(min_length=64, max_length=64)
    item_set_sha256: str = Field(min_length=64, max_length=64)
    required_slots: int = Field(ge=1)
    audio_subjects: int = Field(ge=0)
    visual_subjects: int = Field(ge=0)
    passing: int = Field(ge=0)
    blocked: int = Field(ge=0)
    blockers: tuple[AIAcousticBlocker, ...]
    media_artifacts_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    aggregate_root: str = Field(min_length=64, max_length=64)

    @field_validator(
        "media_rights_sha256",
        "media_authority_sha256",
        "item_set_sha256",
        "media_artifacts_sha256",
        "aggregate_root",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _sha256_text(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def counts_and_hash_must_match(self) -> Self:
        if self.required_slots != 325 or self.audio_subjects != 233 or self.visual_subjects != 92:
            raise ValueError("aggregate counts do not match exact v2 media request")
        if self.passing + self.blocked != self.required_slots:
            raise ValueError("aggregate totals do not cover required slots")
        if self.status == "passing" and (self.blocked or self.blockers):
            raise ValueError("passing aggregate cannot carry blockers")
        if self.status == "passing" and self.media_artifacts_sha256 is None:
            raise ValueError("passing aggregate requires generated artifact binding")
        if self.status == "blocked" and self.blocked <= 0:
            raise ValueError("blocked aggregate requires blockers")
        if self.status == "blocked" and self.media_artifacts_sha256 is not None:
            raise ValueError("blocked aggregate cannot claim generated artifact binding")
        if self.aggregate_root != ai_acoustic_review_sha256(self):
            raise ValueError("aggregate root does not match")
        return self


__all__ = [
    "AIAcousticBlocker",
    "AIAcousticReviewAggregate",
    "AIAcousticReviewDecision",
    "AcousticValidatorRun",
    "ai_acoustic_review_sha256",
]
