"""Typed text-quality contracts for persisted Phase 3 sentence records."""

from __future__ import annotations

from enum import Enum
import math
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_MAX_REPAIR_ATTEMPTS = 2
KOREAN_ADAPTIVE_EVIDENCE_POLICY_VERSION = "korean-adaptive-text-quality-v1"
_MAX_KOREAN_CONCEPT_IDS = 4096
_SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-")


class TextGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    REPAIRED = "repaired"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    NOT_REVIEWED = "not_reviewed"
    REVIEW_REQUIRED = "review_required"
    ACCEPTED = "accepted"


class ValidationFlagCode(str, Enum):
    MISSING_TARGET_LEMMA = "missing_target_lemma"
    SENTENCE_TOO_SHORT = "sentence_too_short"
    SENTENCE_TOO_LONG = "sentence_too_long"
    BANNED_PATTERN = "banned_pattern"
    DUPLICATE_SENTENCE = "duplicate_sentence"
    TRANSLATION_MISMATCH = "translation_mismatch"
    LANGUAGE_MISMATCH = "language_mismatch"
    MORPHOLOGY_MISMATCH = "morphology_mismatch"
    LOW_CONFIDENCE = "low_confidence"


class ConfidenceLabel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationFlag(BaseModel):
    code: ValidationFlagCode
    detail: str = Field(min_length=1)


class TextProvenance(BaseModel):
    source: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


_HEX = frozenset("0123456789abcdef")


def _sha256(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > 160
        or any(character not in _SAFE_IDENTIFIER_CHARS for character in normalized)
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


class _FrozenEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanTextSelectionEvidence(_FrozenEvidence):
    """Machine candidate-selection evidence; never human approval."""

    candidate_set_sha256: str = Field(min_length=64, max_length=64)
    selected_candidate_sha256: str = Field(min_length=64, max_length=64)
    selected_ordinal: int = Field(ge=1)
    initial_candidate_count: int = Field(ge=1, le=2)
    repair_attempt_count: int = Field(ge=0, le=1)
    hard_gate_status: Literal["passed", "failed"]
    selector_version: str = Field(min_length=1, max_length=128)

    @field_validator("candidate_set_sha256", "selected_candidate_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))


class KoreanAdaptiveIPlusOneEvidence(_FrozenEvidence):
    """Adaptive known-state and novelty evidence for Korean frequency text."""

    known_prefix_sha256: str = Field(min_length=64, max_length=64)
    known_concept_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=_MAX_KOREAN_CONCEPT_IDS)
    known_concept_count: int = Field(default=0, ge=0, le=_MAX_KOREAN_CONCEPT_IDS)
    phase31_pointer_locator_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    phase31_pointer_content_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    phase31_validation_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    phase31_snapshot_manifest_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    phase31_snapshot_root_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    frequency_bundle_locator_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    frequency_bundle_content_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    candidate_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    selected_ordinal: int | None = Field(default=None, ge=1)
    hard_gate_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    score_components: dict[str, float] = Field(default_factory=dict)
    policy_version: str = Field(default=KOREAN_ADAPTIVE_EVIDENCE_POLICY_VERSION, min_length=1, max_length=128)
    target_concept_id: str = Field(min_length=1, max_length=128)
    observed_concept_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=_MAX_KOREAN_CONCEPT_IDS)
    incidental_concept_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=_MAX_KOREAN_CONCEPT_IDS)
    scorer_version: str = Field(min_length=1, max_length=128)

    @field_validator(
        "known_prefix_sha256",
        "phase31_pointer_locator_sha256",
        "phase31_pointer_content_sha256",
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "frequency_bundle_locator_sha256",
        "frequency_bundle_content_sha256",
        "candidate_sha256",
    )
    @classmethod
    def hash_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("known_concept_ids", "observed_concept_ids", "incidental_concept_ids")
    @classmethod
    def concept_ids_must_be_safe_and_unique(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "concept ids")
        normalized = tuple(_safe_identifier(item, field_name=field_name) for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError(f"{field_name} must contain unique identifiers")
        return normalized

    @field_validator("target_concept_id")
    @classmethod
    def target_concept_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="target_concept_id")

    @field_validator("hard_gate_codes")
    @classmethod
    def hard_gate_codes_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_safe_identifier(item, field_name="hard_gate_codes") for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("hard_gate_codes must contain unique identifiers")
        return normalized

    @model_validator(mode="after")
    def adaptive_evidence_must_be_deterministic(self) -> Self:
        has_expanded_evidence = any(
            value is not None
            for value in (
                self.phase31_pointer_locator_sha256,
                self.phase31_pointer_content_sha256,
                self.phase31_validation_receipt_sha256,
                self.phase31_snapshot_manifest_sha256,
                self.phase31_snapshot_root_sha256,
                self.frequency_bundle_locator_sha256,
                self.frequency_bundle_content_sha256,
                self.candidate_sha256,
            )
        ) or bool(self.known_concept_ids or self.score_components)
        if self.known_concept_ids and self.known_concept_ids != tuple(sorted(self.known_concept_ids)):
            raise ValueError("known_concept_ids must be canonical sorted identifiers")
        if self.known_concept_ids and self.known_concept_count != len(self.known_concept_ids):
            raise ValueError("known_concept_count must match known_concept_ids")
        if (
            has_expanded_evidence
            and self.incidental_concept_ids
            and not set(self.incidental_concept_ids) <= set(self.observed_concept_ids)
        ):
            raise ValueError("incidental concepts must be observed")
        if self.target_concept_id in self.incidental_concept_ids:
            raise ValueError("target concept cannot be incidental")
        for name, value in self.score_components.items():
            _safe_identifier(name, field_name="score component")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError("score components must be finite numbers")
        return self


class KoreanProviderReviewEvidence(_FrozenEvidence):
    """Provider-review receipt summary distinct from canonical human review state."""

    reviewer_class: Literal["ai_policy_linguistic_review"]
    policy_sha256: str = Field(min_length=64, max_length=64)
    review_receipt_sha256: str = Field(min_length=64, max_length=64)
    decision: Literal["accepted", "rejected", "needs_review"]

    @field_validator("policy_sha256", "review_receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))


class KoreanTextReviewQualification(_FrozenEvidence):
    """Qualified human reviewer identity without raw names or private metadata."""

    reviewer_kind: Literal["human"]
    reviewer_role: Literal["qualified_linguistic_reviewer", "qualified_editorial_reviewer"]
    reviewer_id_sha256: str = Field(min_length=64, max_length=64)
    qualification_policy_sha256: str = Field(min_length=64, max_length=64)
    qualification_receipt_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("reviewer_id_sha256", "qualification_policy_sha256", "qualification_receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))


class KoreanTextReviewCoverage(_FrozenEvidence):
    """Controlled checklist for the exact fields a qualified reviewer inspected."""

    target_identity: bool = Field(strict=True)
    source_sense: bool = Field(strict=True)
    morphology_match: bool = Field(strict=True)
    natural_korean: bool = Field(strict=True)
    pt_br_translation: bool = Field(strict=True)
    adaptive_i_plus_one: bool = Field(strict=True)
    no_private_context: bool = Field(strict=True)
    no_unsafe_markup: bool = Field(strict=True)

    @property
    def is_complete(self) -> bool:
        return all(
            (
                self.target_identity,
                self.source_sense,
                self.morphology_match,
                self.natural_korean,
                self.pt_br_translation,
                self.adaptive_i_plus_one,
                self.no_private_context,
                self.no_unsafe_markup,
            )
        )


class KoreanTextReviewDecision(_FrozenEvidence):
    """Immutable reviewer decision bound to exact hashed production evidence."""

    production_run_sha256: str = Field(min_length=64, max_length=64)
    job_sha256: str = Field(min_length=64, max_length=64)
    run_sha256: str = Field(min_length=64, max_length=64)
    item_sha256: str = Field(min_length=64, max_length=64)
    candidate_sha256: str = Field(min_length=64, max_length=64)
    candidate_identity_sha256: str = Field(min_length=64, max_length=64)
    reviewed_identity_sha256: str = Field(min_length=64, max_length=64)
    policy_sha256: str = Field(min_length=64, max_length=64)
    evidence_root_sha256: str = Field(min_length=64, max_length=64)
    reviewer: KoreanTextReviewQualification
    coverage: KoreanTextReviewCoverage
    outcome: Literal["accepted", "rejected"]
    rejection_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    authority_scope: Literal["review_record_only"] = "review_record_only"

    @field_validator(
        "production_run_sha256",
        "job_sha256",
        "run_sha256",
        "item_sha256",
        "candidate_sha256",
        "candidate_identity_sha256",
        "reviewed_identity_sha256",
        "policy_sha256",
        "evidence_root_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("rejection_codes")
    @classmethod
    def rejection_codes_must_be_controlled(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_safe_identifier(item, field_name="rejection_codes") for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("rejection_codes must contain unique identifiers")
        return normalized

    @model_validator(mode="after")
    def decision_must_not_contradict_bound_evidence(self) -> Self:
        if self.candidate_identity_sha256 != self.reviewed_identity_sha256:
            raise ValueError("stale Korean identity review decision")
        if self.outcome == "accepted":
            if self.rejection_codes:
                raise ValueError("accepted decision cannot carry rejection codes")
            if not self.coverage.is_complete:
                raise ValueError("accepted decision requires complete coverage")
        elif not self.rejection_codes:
            raise ValueError("rejected decision requires rejection codes")
        return self

    @property
    def can_mutate_database(self) -> bool:
        return False

    @property
    def can_promote_or_export(self) -> bool:
        return False


class KoreanTextReviewRejection(KoreanTextReviewDecision):
    """Typed rejection receipt; executable application is owned by later review work."""

    outcome: Literal["rejected"] = "rejected"
    rejection_codes: tuple[str, ...] = Field(min_length=1, max_length=16)


class TextQualityRecord(BaseModel):
    job_id: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    lexical_candidate_id: str = Field(min_length=1)
    example_sentence: str | None = None
    translation_text: str | None = None
    generation_status: TextGenerationStatus
    validation_status: ValidationStatus
    review_status: ReviewStatus
    repair_attempt_count: int = Field(default=0, ge=0)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel
    validation_flags: list[ValidationFlag] = Field(default_factory=list)
    review_reason: str | None = None
    sentence_provenance: TextProvenance
    translation_provenance: TextProvenance
    candidate_selection_evidence: KoreanTextSelectionEvidence | None = None
    adaptive_i_plus_one_evidence: KoreanAdaptiveIPlusOneEvidence | None = None
    provider_review_evidence: KoreanProviderReviewEvidence | None = None
    text_review_receipt_sha256: str | None = None

    @field_validator("text_review_receipt_sha256")
    @classmethod
    def review_receipt_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _sha256(value, field_name="text_review_receipt_sha256")

    @model_validator(mode="after")
    def phase32_machine_evidence_must_not_self_approve(self) -> Self:
        has_phase32_evidence = any(
            value is not None
            for value in (
                self.candidate_selection_evidence,
                self.adaptive_i_plus_one_evidence,
                self.provider_review_evidence,
                self.text_review_receipt_sha256,
            )
        )
        if not has_phase32_evidence:
            return self
        if self.review_status is ReviewStatus.ACCEPTED:
            if self.text_review_receipt_sha256 is None:
                raise ValueError("Korean accepted text requires an exact review receipt")
            if self.provider_review_evidence is not None and self.provider_review_evidence.decision != "accepted":
                raise ValueError("Korean accepted text requires accepted provider review evidence")
        return self

    @property
    def requires_review(self) -> bool:
        return self.review_status is ReviewStatus.REVIEW_REQUIRED or (
            self.validation_status is ValidationStatus.FAILED and not self.can_attempt_repair()
        )

    @property
    def stage_flow(self) -> str:
        if self.generation_status is TextGenerationStatus.PENDING:
            return "generate"
        if self.validation_status is ValidationStatus.PENDING:
            return "validate"
        if self.validation_status is ValidationStatus.FAILED and self.can_attempt_repair():
            return "repair"
        if self.requires_review:
            return "review"
        return "complete"

    def can_attempt_repair(self, *, max_attempts: int = DEFAULT_MAX_REPAIR_ATTEMPTS) -> bool:
        return self.repair_attempt_count < max_attempts


__all__ = [
    "DEFAULT_MAX_REPAIR_ATTEMPTS",
    "ConfidenceLabel",
    "KOREAN_ADAPTIVE_EVIDENCE_POLICY_VERSION",
    "KoreanAdaptiveIPlusOneEvidence",
    "KoreanProviderReviewEvidence",
    "KoreanTextReviewCoverage",
    "KoreanTextReviewDecision",
    "KoreanTextReviewQualification",
    "KoreanTextReviewRejection",
    "KoreanTextSelectionEvidence",
    "ReviewStatus",
    "TextGenerationStatus",
    "TextProvenance",
    "TextQualityRecord",
    "ValidationFlag",
    "ValidationFlagCode",
    "ValidationStatus",
]
