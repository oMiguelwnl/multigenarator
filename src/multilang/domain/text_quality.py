"""Typed text-quality contracts for persisted Phase 3 sentence records."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_MAX_REPAIR_ATTEMPTS = 2


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
    target_concept_id: str = Field(min_length=1, max_length=128)
    observed_concept_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    incidental_concept_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    scorer_version: str = Field(min_length=1, max_length=128)

    @field_validator("known_prefix_sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256(value, field_name="known_prefix_sha256")


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
    "KoreanAdaptiveIPlusOneEvidence",
    "KoreanProviderReviewEvidence",
    "KoreanTextSelectionEvidence",
    "ReviewStatus",
    "TextGenerationStatus",
    "TextProvenance",
    "TextQualityRecord",
    "ValidationFlag",
    "ValidationFlagCode",
    "ValidationStatus",
]
