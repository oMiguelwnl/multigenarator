"""Typed text-quality contracts for persisted Phase 3 sentence records."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

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
    "ReviewStatus",
    "TextGenerationStatus",
    "TextProvenance",
    "TextQualityRecord",
    "ValidationFlag",
    "ValidationFlagCode",
    "ValidationStatus",
]
