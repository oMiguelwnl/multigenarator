"""Immutable field revision and review contracts.

The models in this module are pure contracts: they do not call providers, mutate
stored history, or carry private values in events.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator


AI_LINGUISTIC_POLICY_ID = "multilang-ai-linguistic-review-v1"

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_EXTENSION = re.compile(r"^[a-z0-9][a-z0-9]{0,15}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    return value


def canonical_command_sha256(value: object) -> str:
    """Hash exact command/query data with canonical JSON."""

    encoded = json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def review_content_sha256(value: object) -> str:
    """Hash a model payload while excluding a top-level content hash field."""

    payload = _jsonable(value)
    if isinstance(payload, dict):
        payload = dict(payload)
        payload.pop("content_hash", None)
    return canonical_command_sha256(payload)


def _hash(value: str, field_name: str = "sha256") -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _identifier(value: str, field_name: str = "identifier") -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a bounded safe identifier")
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"{field_name} must be a safe path segment")
    return value


def _timestamp(value: str) -> str:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise ValueError("timestamp must be UTC second precision")
    return value


def _unique_identifiers(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_identifier(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must be unique")
    return normalized


def _freeze_json(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, tuple | list):
        return tuple(_freeze_json(item) for item in value)
    return value


class _FrozenReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ReviewField(str, Enum):
    DEFINITION = "definition"
    SENTENCE = "sentence"
    TRANSLATION = "translation"
    WORD_AUDIO = "word_audio"
    SENTENCE_AUDIO = "sentence_audio"

    @property
    def is_audio(self) -> bool:
        return self in {ReviewField.WORD_AUDIO, ReviewField.SENTENCE_AUDIO}


class ReviewStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    STALE = "stale"


class ReviewAccessAction(str, Enum):
    LIST = "list"
    INSPECT = "inspect"
    PRIVATE_DISPLAY = "private_display"


class ReviewTransitionAction(str, Enum):
    CREATE_CANDIDATE = "create_candidate"
    VALIDATED_GENERATION_RESULT = "validated_generation_result"
    EDIT_TO_NEW_CANDIDATE = "edit_to_new_candidate"
    REGENERATE_FIELD = "regenerate_field"
    APPROVE = "approve"
    REJECT = "reject"
    STALE_DEPENDENT = "stale_dependent"
    BRIDGE = "bridge"
    DEFER = "defer"
    AUDIO_RESERVED = "audio_reserved"
    AUDIO_STAGED = "audio_staged"
    AUDIO_PUBLISHED = "audio_published"
    AUDIO_FINALIZED = "audio_finalized"


class AudioPublicationStatus(str, Enum):
    RESERVED = "reserved"
    STAGED = "staged"
    PUBLISHED = "published"
    FINALIZED = "finalized"
    FAILED_UNKNOWN = "failed_unknown"
    BLOCKED_MISMATCH = "blocked_mismatch"


class HashBinding(_FrozenReviewModel):
    name: str = Field(min_length=1, max_length=128)
    sha256: str

    @field_validator("name")
    @classmethod
    def name_must_be_safe(cls, value: str) -> str:
        return _identifier(value, field_name="hash binding name")

    @field_validator("sha256")
    @classmethod
    def sha256_must_be_hash(cls, value: str) -> str:
        return _hash(value)


class FieldDependencyBinding(_FrozenReviewModel):
    source_field: ReviewField
    source_revision_id: str
    source_revision_no: int = Field(ge=1)
    source_content_hash: str
    relation: Literal[
        "grounded_in",
        "translated_from",
        "audio_of",
        "policy",
        "source_identity",
    ]

    @field_validator("source_revision_id")
    @classmethod
    def revision_id_must_be_safe(cls, value: str) -> str:
        return _identifier(value, field_name="source revision id")

    @field_validator("source_content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _hash(value, field_name="source content hash")


class GeneratorMetadata(_FrozenReviewModel):
    generator_id: str
    generator_version: str
    route_id: str | None = None
    request_sha256: str | None = None

    @field_validator("generator_id", "generator_version", "route_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _identifier(value)

    @field_validator("request_sha256")
    @classmethod
    def request_hash_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _hash(value, field_name="request sha256")


class RevisionCreationEvidence(_FrozenReviewModel):
    actor_type: Literal["generator", "local_user", "system", "ai_model"]
    actor_id: str
    source_kind: Literal["generated", "synthetic", "edited", "imported", "audio_publication"]
    created_at: str
    evidence_sha256: str

    @field_validator("actor_id")
    @classmethod
    def actor_id_must_be_safe(cls, value: str) -> str:
        return _identifier(value, field_name="actor id")

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @field_validator("evidence_sha256")
    @classmethod
    def evidence_hash_must_be_sha256(cls, value: str) -> str:
        return _hash(value, field_name="evidence sha256")


class FieldRevision(_FrozenReviewModel):
    job_id: str
    item_id: str
    field: ReviewField
    revision_id: str
    revision_no: int = Field(ge=1)
    content_hash: str
    payload: Mapping[str, Any]
    source_hashes: tuple[HashBinding, ...] = ()
    dependency_hashes: tuple[FieldDependencyBinding, ...] = ()
    generator: GeneratorMetadata
    creation_evidence: RevisionCreationEvidence
    initial_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    created_at: str

    @field_validator("job_id", "item_id", "revision_id")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("content_hash")
    @classmethod
    def content_hash_must_be_sha256(cls, value: str) -> str:
        return _hash(value, field_name="content hash")

    @field_validator("payload")
    @classmethod
    def payload_must_be_private_envelope(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        if not value:
            raise ValueError("payload must be a non-empty value envelope")
        return _freeze_json(value)  # type: ignore[return-value]

    @field_serializer("payload")
    def serialize_payload(self, value: Mapping[str, Any]) -> dict[str, object]:
        return _jsonable(value)  # type: ignore[return-value]

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def generated_content_cannot_start_accepted(self) -> Self:
        if (
            self.creation_evidence.source_kind in {"generated", "synthetic", "edited", "audio_publication"}
            and self.initial_status is ReviewStatus.ACCEPTED
        ):
            raise ValueError("generated content cannot start accepted")
        names = tuple(binding.name for binding in self.source_hashes)
        if len(names) != len(set(names)):
            raise ValueError("source hash names must be unique")
        return self


class FieldPointer(_FrozenReviewModel):
    job_id: str
    item_id: str
    field: ReviewField
    candidate_revision_id: str | None = None
    candidate_content_hash: str | None = None
    approved_revision_id: str | None = None
    approved_content_hash: str | None = None
    version: int = Field(ge=0)

    @field_validator("job_id", "item_id", "candidate_revision_id", "approved_revision_id")
    @classmethod
    def ids_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _identifier(value)

    @field_validator("candidate_content_hash", "approved_content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _hash(value)

    @model_validator(mode="after")
    def pointer_hashes_must_match_ids(self) -> Self:
        if (self.candidate_revision_id is None) != (self.candidate_content_hash is None):
            raise ValueError("candidate pointer must include revision and hash together")
        if (self.approved_revision_id is None) != (self.approved_content_hash is None):
            raise ValueError("approved pointer must include revision and hash together")
        return self

    @property
    def candidate_identity(self) -> tuple[str, str] | None:
        if self.candidate_revision_id is None or self.candidate_content_hash is None:
            return None
        return (self.candidate_revision_id, self.candidate_content_hash)

    @property
    def approved_identity(self) -> tuple[str, str] | None:
        if self.approved_revision_id is None or self.approved_content_hash is None:
            return None
        return (self.approved_revision_id, self.approved_content_hash)


class ReviewValidatorOutcome(_FrozenReviewModel):
    validator_id: str
    validator_version: str
    result: Literal["passed", "failed", "inconclusive"]
    reason_code: str
    output_sha256: str
    executed_at: str

    @field_validator("validator_id", "validator_version", "reason_code")
    @classmethod
    def codes_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("output_sha256")
    @classmethod
    def output_hash_must_be_sha256(cls, value: str) -> str:
        return _hash(value, field_name="validator output sha256")

    @field_validator("executed_at")
    @classmethod
    def executed_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def validator_reason_must_match_result(self) -> Self:
        if (self.result == "passed") != (self.reason_code == "none"):
            raise ValueError("validator reason must match result")
        return self


class AIReviewPass(_FrozenReviewModel):
    pass_id: str
    fresh_context_id: str
    provider_id: str
    model_id: str
    route_id: str
    prompt_sha256: str
    output_schema_sha256: str
    decision: Literal["passed", "failed", "uncertain"]
    reason_code: str
    uncertainty_codes: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    started_at: str
    completed_at: str

    @field_validator("pass_id", "fresh_context_id", "provider_id", "model_id", "route_id", "reason_code")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("uncertainty_codes")
    @classmethod
    def uncertainty_codes_must_be_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_identifiers(values, field_name="uncertainty code")

    @field_validator("prompt_sha256", "output_schema_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_must_be_valid(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def pass_state_must_be_consistent(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("review pass time order invalid")
        if self.decision == "passed" and (
            self.reason_code != "none" or self.uncertainty_codes or self.confidence < 0.8
        ):
            raise ValueError("passed review pass invalid")
        if self.decision == "failed" and (self.reason_code == "none" or self.uncertainty_codes):
            raise ValueError("failed review pass invalid")
        if self.decision == "uncertain" and (
            self.reason_code == "none" or not self.uncertainty_codes
        ):
            raise ValueError("uncertain review pass invalid")
        return self


class AILinguisticReviewEvidence(_FrozenReviewModel):
    evidence_id: str
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    policy_sha256: str
    provider_id: str
    model_id: str
    route_id: str
    prompt_id: str
    prompt_sha256: str
    output_schema_id: str
    output_schema_sha256: str
    source_sha256: str
    candidate_sha256: str
    analyzer_sha256: str
    curriculum_sha256: str
    media_sha256: str
    validator_outcomes: tuple[ReviewValidatorOutcome, ...] = Field(min_length=1)
    passes: tuple[AIReviewPass, ...] = Field(min_length=2, max_length=3)
    required_pass_count: Literal[2, 3]
    status: Literal[
        "ai_review_passed",
        "ai_review_failed",
        "blocked_uncertainty",
        "blocked_disagreement",
        "stale",
    ]
    reason_code: str
    uncertainty_codes: tuple[str, ...] = ()
    source_kind: Literal["production", "synthetic"] = "production"
    orchestrated_at: str

    @field_validator(
        "evidence_id",
        "provider_id",
        "model_id",
        "route_id",
        "prompt_id",
        "output_schema_id",
        "reason_code",
    )
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator(
        "policy_sha256",
        "prompt_sha256",
        "output_schema_sha256",
        "source_sha256",
        "candidate_sha256",
        "analyzer_sha256",
        "curriculum_sha256",
        "media_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)

    @field_validator("uncertainty_codes")
    @classmethod
    def uncertainty_codes_must_be_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_identifiers(values, field_name="uncertainty code")

    @field_validator("orchestrated_at")
    @classmethod
    def orchestrated_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def evidence_must_satisfy_policy(self) -> Self:
        if len(self.passes) != self.required_pass_count:
            raise ValueError("AI review evidence requires exact pass count")
        if len({review.pass_id for review in self.passes}) != len(self.passes):
            raise ValueError("AI review pass identities must be unique")
        if len({review.fresh_context_id for review in self.passes}) != len(self.passes):
            raise ValueError("AI review fresh contexts must be unique")
        if any(outcome.result != "passed" for outcome in self.validator_outcomes):
            if self.status == "ai_review_passed":
                raise ValueError("deterministic failure cannot be accepted")
            return self

        pass_decisions = {review.decision for review in self.passes}
        if pass_decisions == {"passed"}:
            expected = "ai_review_passed"
        elif "uncertain" in pass_decisions:
            expected = "blocked_uncertainty"
        else:
            expected = "blocked_disagreement"
        if self.status != expected:
            raise ValueError("AI review consensus status invalid")
        if self.status == "ai_review_passed" and (self.reason_code != "none" or self.uncertainty_codes):
            raise ValueError("passed AI review evidence invalid")
        if self.status != "ai_review_passed" and self.reason_code == "none":
            raise ValueError("blocked AI review evidence requires reason")
        return self


class AudioReviewEvidence(_FrozenReviewModel):
    evidence_id: str
    status: Literal[
        "ai_acoustic_review_passed",
        "automated_integrity_passed",
        "audio_review_failed",
        "blocked_mismatch",
        "stale",
    ]
    policy_sha256: str
    integrity_sha256: str
    request_sha256: str
    profile_sha256: str
    artifact_sha256: str
    final_path: str
    revision_content_sha256: str
    acoustic_review_sha256: str | None = None
    human_heard_claim: Literal[False] = False
    source_kind: Literal["production", "synthetic"] = "production"

    @field_validator("evidence_id")
    @classmethod
    def evidence_id_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator(
        "policy_sha256",
        "integrity_sha256",
        "request_sha256",
        "profile_sha256",
        "artifact_sha256",
        "revision_content_sha256",
        "acoustic_review_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _hash(value)

    @model_validator(mode="after")
    def audio_acceptance_must_be_exact(self) -> Self:
        if self.status == "ai_acoustic_review_passed" and self.acoustic_review_sha256 is None:
            raise ValueError("AI acoustic review evidence requires acoustic hash")
        if self.status in {"ai_acoustic_review_passed", "automated_integrity_passed"} and self.final_path.startswith("/"):
            raise ValueError("audio final path must be relative")
        return self


class ReviewDecision(_FrozenReviewModel):
    decision_id: str
    job_id: str
    item_id: str
    field: ReviewField
    revision_id: str
    revision_no: int = Field(ge=1)
    content_hash: str
    status: ReviewStatus
    actor_type: Literal["ai_model", "system", "local_user"]
    actor_id: str
    policy_sha256: str
    evidence: AILinguisticReviewEvidence | AudioReviewEvidence | None = None
    reason_code: str
    dependency_binding: FieldDependencyBinding | None = None
    created_at: str

    @field_validator("decision_id", "job_id", "item_id", "revision_id", "actor_id", "reason_code")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("content_hash", "policy_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def decision_must_match_status_and_evidence(self) -> Self:
        if self.status is ReviewStatus.ACCEPTED:
            if self.evidence is None:
                raise ValueError("accepted decision requires evidence")
            if getattr(self.evidence, "source_kind", "production") != "production":
                raise ValueError("accepted decision cannot use synthetic evidence")
            if self.reason_code != "none":
                raise ValueError("accepted decision reason must be none")
            if self.field.is_audio:
                if not isinstance(self.evidence, AudioReviewEvidence):
                    raise ValueError("audio acceptance requires audio evidence")
                if self.evidence.status not in {"ai_acoustic_review_passed", "automated_integrity_passed"}:
                    raise ValueError("audio acceptance evidence did not pass")
                if self.evidence.revision_content_sha256 != self.content_hash:
                    raise ValueError("audio evidence content hash mismatch")
            else:
                if not isinstance(self.evidence, AILinguisticReviewEvidence):
                    raise ValueError("text acceptance requires AI linguistic evidence")
                if self.evidence.status != "ai_review_passed":
                    raise ValueError("AI linguistic evidence did not pass")
                if self.evidence.candidate_sha256 != self.content_hash:
                    raise ValueError("AI evidence content hash mismatch")
        elif self.status is ReviewStatus.REJECTED and self.reason_code == "none":
            raise ValueError("rejected decision requires reason")
        elif self.status is ReviewStatus.STALE:
            if self.reason_code == "none" or self.dependency_binding is None:
                raise ValueError("stale decision requires dependency and reason")
        return self


class ReviewListSelector(_FrozenReviewModel):
    job_id: str
    fields: tuple[ReviewField, ...] = Field(min_length=1)
    statuses: tuple[ReviewStatus, ...] = Field(min_length=1)
    source_types: tuple[str, ...] = Field(min_length=1)
    snapshot_sha256: str
    policy_sha256: str

    @field_validator("job_id")
    @classmethod
    def job_id_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("source_types")
    @classmethod
    def source_types_must_be_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _unique_identifiers(values, field_name="source type")

    @field_validator("snapshot_sha256", "policy_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)


class ReviewInspectSelector(_FrozenReviewModel):
    job_id: str
    item_id: str
    field: ReviewField
    revision_id: str
    pointer_version: int = Field(ge=0)
    policy_sha256: str

    @field_validator("job_id", "item_id", "revision_id")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("policy_sha256")
    @classmethod
    def policy_hash_must_be_sha256(cls, value: str) -> str:
        return _hash(value)


class PrivateDisplaySelector(ReviewInspectSelector):
    local_acknowledgement: Literal[True]


class ReviewAccessEvent(_FrozenReviewModel):
    event_id: str
    actor_id: str
    request_id: str
    action: ReviewAccessAction
    command_sha256: str
    result_id: str
    result_hash: str
    result_count: int = Field(ge=0)
    occurred_at: str

    @field_validator("event_id", "actor_id", "request_id", "result_id")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("command_sha256", "result_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @property
    def stable_identity(self) -> tuple[str, str, ReviewAccessAction]:
        return (self.actor_id, self.request_id, self.action)


class ReviewTransitionEvent(_FrozenReviewModel):
    event_id: str
    job_id: str
    item_id: str
    field: ReviewField | None = None
    action: ReviewTransitionAction
    actor_id: str
    request_id: str
    command_sha256: str
    before_revision_id: str | None = None
    before_content_hash: str | None = None
    after_revision_id: str | None = None
    after_content_hash: str | None = None
    before_pointer_version: int = Field(ge=0)
    after_pointer_version: int = Field(ge=0)
    reason_code: str
    occurred_at: str

    @field_validator(
        "event_id",
        "job_id",
        "item_id",
        "actor_id",
        "request_id",
        "before_revision_id",
        "after_revision_id",
        "reason_code",
    )
    @classmethod
    def ids_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _identifier(value)

    @field_validator("command_sha256", "before_content_hash", "after_content_hash")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _hash(value)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)


def derive_audio_final_path(
    *,
    field: ReviewField,
    item_id: str,
    revision_id: str,
    request_sha256: str,
    profile_extension: str,
) -> str:
    field = ReviewField(field)
    if not field.is_audio:
        raise ValueError("audio final path requires an audio field")
    safe_item_id = _identifier(item_id, field_name="item id")
    safe_revision_id = _identifier(revision_id, field_name="revision id")
    request_hash = _hash(request_sha256, field_name="request sha256")
    extension = profile_extension.lower().removeprefix(".")
    if _EXTENSION.fullmatch(extension) is None:
        raise ValueError("profile extension must be profile-approved and safe")
    return f"{field.value}/{safe_item_id}/{safe_revision_id}/{request_hash}.{extension}"


class AudioPublicationReservation(_FrozenReviewModel):
    reservation_id: str
    job_id: str
    item_id: str
    field: ReviewField
    revision_id: str
    revision_no: int = Field(ge=1)
    revision_content_hash: str
    request_sha256: str
    profile_extension: str
    final_path: str
    authority_sha256: str
    root_prestate_sha256: str
    version: int = Field(ge=1)
    reserved_at: str

    @field_validator("reservation_id", "job_id", "item_id", "revision_id")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator(
        "revision_content_hash",
        "request_sha256",
        "authority_sha256",
        "root_prestate_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str) -> str:
        return _hash(value)

    @field_validator("reserved_at")
    @classmethod
    def reserved_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def final_path_must_match_identity(self) -> Self:
        expected = derive_audio_final_path(
            field=self.field,
            item_id=self.item_id,
            revision_id=self.revision_id,
            request_sha256=self.request_sha256,
            profile_extension=self.profile_extension,
        )
        if self.final_path != expected:
            raise ValueError("final path must match reservation identity")
        return self


class AudioPublicationTransition(_FrozenReviewModel):
    transition_id: str
    reservation_id: str
    status: AudioPublicationStatus
    from_version: int = Field(ge=0)
    to_version: int = Field(ge=1)
    final_path: str
    artifact_sha256: str | None = None
    evidence_sha256: str
    reason_code: str
    occurred_at: str

    @field_validator("transition_id", "reservation_id", "reason_code")
    @classmethod
    def ids_must_be_safe(cls, value: str) -> str:
        return _identifier(value)

    @field_validator("artifact_sha256", "evidence_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _hash(value)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timestamp(cls, value: str) -> str:
        return _timestamp(value)

    @model_validator(mode="after")
    def transition_version_must_advance_once(self) -> Self:
        if self.to_version != self.from_version + 1:
            raise ValueError("publication transition must advance one version")
        if self.status in {AudioPublicationStatus.PUBLISHED, AudioPublicationStatus.FINALIZED} and self.artifact_sha256 is None:
            raise ValueError("published audio transition requires artifact hash")
        return self


__all__ = [
    "AI_LINGUISTIC_POLICY_ID",
    "AILinguisticReviewEvidence",
    "AIReviewPass",
    "AudioPublicationReservation",
    "AudioPublicationStatus",
    "AudioPublicationTransition",
    "AudioReviewEvidence",
    "FieldDependencyBinding",
    "FieldPointer",
    "FieldRevision",
    "GeneratorMetadata",
    "HashBinding",
    "PrivateDisplaySelector",
    "ReviewAccessAction",
    "ReviewAccessEvent",
    "ReviewDecision",
    "ReviewField",
    "ReviewInspectSelector",
    "ReviewListSelector",
    "ReviewStatus",
    "ReviewTransitionAction",
    "ReviewTransitionEvent",
    "ReviewValidatorOutcome",
    "RevisionCreationEvidence",
    "canonical_command_sha256",
    "derive_audio_final_path",
    "review_content_sha256",
]
