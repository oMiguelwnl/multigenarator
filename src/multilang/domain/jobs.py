"""Core job orchestration contracts for Phase 1."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.source_profiles import SourceType


class SupportedLanguage(str, Enum):
    PT = "pt"
    ES = "es"
    EN = "en"
    FR = "fr"
    DE = "de"
    EL = "el"
    IT = "it"
    PL = "pl"
    TR = "tr"
    RO = "ro"
    RU = "ru"
    NL = "nl"
    DA = "da"
    NB = "nb"
    SV = "sv"
    FI = "fi"
    HU = "hu"
    CS = "cs"
    HR = "hr"
    LA = "la"
    JA = "ja"
    ZH = "zh"
    KO = "ko"


class JobStage(str, Enum):
    INGEST = "ingest"
    ENRICH = "enrich"
    GENERATE_TEXT = "generate_text"
    SYNTHESIZE_AUDIO = "synthesize_audio"
    EXPORT = "export"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ItemTerminalStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"


class ControlledReasonCode(str, Enum):
    ITEM_LOCAL_EXCEPTION = "item_local_exception"
    REVIEW_OUTSTANDING = "review_outstanding"
    MEDIA_OUTSTANDING = "media_outstanding"
    VALIDATION_FAILED = "validation_failed"
    DUPLICATE = "duplicate"
    DEFERRED = "deferred"
    RETRY_EXHAUSTED = "retry_exhausted"
    FAILED_UNKNOWN = "failed_unknown"
    SYSTEMIC_FAILURE = "systemic_failure"


class ItemDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reason_code: ControlledReasonCode
    correlation_id: str | None = Field(default=None, min_length=1)


class FieldObligationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ai_review_current: bool = True
    integrity_current: bool = True
    word_audio_required: bool = False
    word_audio_current: bool = True
    sentence_audio_required: bool = False
    sentence_audio_current: bool = True

    @property
    def all_required_current(self) -> bool:
        return (
            self.ai_review_current
            and self.integrity_current
            and (not self.word_audio_required or self.word_audio_current)
            and (not self.sentence_audio_required or self.sentence_audio_current)
        )

    @property
    def has_outstanding_work(self) -> bool:
        return not self.all_required_current


class ItemAttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_number: int = Field(ge=1)
    attempted_at: datetime
    processed_at: datetime | None = None

    @model_validator(mode="after")
    def processed_cannot_precede_attempt(self) -> "ItemAttemptRecord":
        if self.processed_at is not None and self.processed_at < self.attempted_at:
            raise ValueError("processed_at cannot be before attempted_at")
        return self


class ItemOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    status: ItemTerminalStatus
    attempts: tuple[ItemAttemptRecord, ...] = ()
    obligations: FieldObligationSummary = Field(default_factory=FieldObligationSummary)
    diagnostic: ItemDiagnostic | None = None

    @model_validator(mode="after")
    def status_matches_attempt_and_obligation_facts(self) -> "ItemOutcome":
        if self.status is ItemTerminalStatus.PENDING and self.attempts:
            raise ValueError("pending items cannot have attempts")
        if self.status is ItemTerminalStatus.PROCESSING:
            if not self.attempts or self.attempts[-1].processed_at is not None:
                raise ValueError("processing items require an open current attempt")
        if self.status is ItemTerminalStatus.ACCEPTED:
            if "obligations" not in self.model_fields_set:
                raise ValueError("accepted items require explicit obligation evidence")
            if not self.obligations.all_required_current:
                raise ValueError("accepted items require current review and media evidence")
            if self.attempts and self.attempts[-1].processed_at is None:
                raise ValueError("accepted attempted items require processed_at")
        return self

    @property
    def attempted_at(self) -> datetime | None:
        if not self.attempts:
            return None
        return self.attempts[-1].attempted_at

    @property
    def processed_at(self) -> datetime | None:
        if not self.attempts:
            return None
        return self.attempts[-1].processed_at

    @property
    def was_attempted(self) -> bool:
        return bool(self.attempts)

    @property
    def was_processed(self) -> bool:
        return any(attempt.processed_at is not None for attempt in self.attempts)


class ItemRunReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eligible_item_ids: tuple[str, ...]
    attempted_item_ids: tuple[str, ...]
    processed_item_ids: tuple[str, ...]
    skipped_current_item_ids: tuple[str, ...]
    not_attempted_item_ids: tuple[str, ...]
    accepted_item_ids: tuple[str, ...]
    review_required_item_ids: tuple[str, ...]
    failed_item_ids: tuple[str, ...]
    duplicate_item_ids: tuple[str, ...] = ()
    deferred_item_ids: tuple[str, ...] = ()
    field_obligations: dict[str, FieldObligationSummary] = Field(default_factory=dict)

    @model_validator(mode="after")
    def counts_must_match_outcome_algebra(self) -> "ItemRunReport":
        eligible = _unique_ids("eligible_item_ids", self.eligible_item_ids)
        attempted = _unique_ids("attempted_item_ids", self.attempted_item_ids)
        processed = _unique_ids("processed_item_ids", self.processed_item_ids)
        skipped = _unique_ids("skipped_current_item_ids", self.skipped_current_item_ids)
        not_attempted = _unique_ids("not_attempted_item_ids", self.not_attempted_item_ids)
        accepted = _unique_ids("accepted_item_ids", self.accepted_item_ids)
        review_required = _unique_ids("review_required_item_ids", self.review_required_item_ids)
        failed = _unique_ids("failed_item_ids", self.failed_item_ids)
        duplicate = _unique_ids("duplicate_item_ids", self.duplicate_item_ids)
        deferred = _unique_ids("deferred_item_ids", self.deferred_item_ids)

        if attempted & skipped or attempted & not_attempted or skipped & not_attempted:
            raise ValueError("attempted, skipped_current, and not_attempted must be disjoint")
        if attempted | skipped | not_attempted != eligible:
            raise ValueError("attempted/skipped_current/not_attempted must partition eligible items")
        if not processed <= attempted:
            raise ValueError("processed items must be a subset of attempted items")
        if not accepted <= eligible or not review_required <= eligible or not failed <= eligible:
            raise ValueError("terminal status item IDs must be eligible")
        if accepted & review_required or accepted & failed or review_required & failed:
            raise ValueError("accepted, review_required, and failed item IDs must be disjoint")
        if not accepted <= processed | skipped:
            raise ValueError("accepted items must be processed in-run or skipped as already current")
        if not duplicate <= not_attempted or not deferred <= not_attempted:
            raise ValueError("duplicate and deferred items must be explicit not_attempted items")
        if duplicate & deferred:
            raise ValueError("duplicate and deferred item IDs must be disjoint")
        for item_id in accepted:
            obligations = self.field_obligations.get(item_id)
            if obligations is None or not obligations.all_required_current:
                raise ValueError("accepted items require exact current obligation evidence")
        return self

    @property
    def total_eligible(self) -> int:
        return len(self.eligible_item_ids)

    @property
    def attempted(self) -> int:
        return len(self.attempted_item_ids)

    @property
    def processed(self) -> int:
        return len(self.processed_item_ids)

    @property
    def accepted(self) -> int:
        return len(self.accepted_item_ids)

    @property
    def review_required(self) -> int:
        return len(self.review_required_item_ids)

    @property
    def failed(self) -> int:
        return len(self.failed_item_ids)

    @property
    def skipped_current(self) -> int:
        return len(self.skipped_current_item_ids)

    @property
    def not_attempted(self) -> int:
        return len(self.not_attempted_item_ids)

    @property
    def counts(self) -> dict[str, int]:
        return {
            "total_eligible": self.total_eligible,
            "attempted": self.attempted,
            "processed": self.processed,
            "accepted": self.accepted,
            "review_required": self.review_required,
            "failed": self.failed,
            "skipped_current": self.skipped_current,
            "not_attempted": self.not_attempted,
            "duplicate": len(self.duplicate_item_ids),
            "deferred": len(self.deferred_item_ids),
        }

    @property
    def is_complete(self) -> bool:
        if self.review_required_item_ids or self.failed_item_ids or self.not_attempted_item_ids:
            return False
        if self.duplicate_item_ids or self.deferred_item_ids:
            return False
        if set(self.accepted_item_ids) != set(self.eligible_item_ids):
            return False
        return all(
            self.field_obligations[item_id].all_required_current
            for item_id in self.accepted_item_ids
        )

    @property
    def is_resumable(self) -> bool:
        return not self.is_complete


def _unique_ids(field_name: str, item_ids: tuple[str, ...]) -> set[str]:
    if len(item_ids) != len(set(item_ids)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(not item_id for item_id in item_ids):
        raise ValueError(f"{field_name} must not contain blank IDs")
    return set(item_ids)


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=2, ge=1)


class GenerationRequest(BaseModel):
    language: SupportedLanguage
    source_type: SourceType
    level: int | None = Field(default=None, ge=1, le=3)
    cards_per_level: int | None = Field(default=None, ge=1)
    input_file: Path | None = None
    resume_job_id: str | None = None
    overwrite: bool = False
    yes_overwrite: bool = False
    missing_only: bool = False
    max_items: int | None = Field(default=None, ge=1)
    rate_limit_per_minute: int | None = Field(default=None, ge=1)
    concurrency: int = Field(default=1, ge=1)

    def resolved_cards_per_level(self) -> int:
        if self.cards_per_level is not None:
            return self.cards_per_level
        return 1000


class JobProgressSnapshot(BaseModel):
    stage: JobStage
    completed_items: int = Field(default=0, ge=0)
    failed_items: int = Field(default=0, ge=0)
    retrying_items: int = Field(default=0, ge=0)
    skipped_duplicates: int = Field(default=0, ge=0)


class ResumeDiagnostic(BaseModel):
    job_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        reason = value.strip()
        if not reason:
            raise ValueError("reason must not be blank")
        return reason


__all__ = [
    "ControlledReasonCode",
    "FieldObligationSummary",
    "GenerationRequest",
    "ItemAttemptRecord",
    "ItemDiagnostic",
    "ItemOutcome",
    "ItemRunReport",
    "ItemTerminalStatus",
    "JobProgressSnapshot",
    "JobStage",
    "JobStatus",
    "ResumeDiagnostic",
    "RetryPolicy",
    "SupportedLanguage",
]
