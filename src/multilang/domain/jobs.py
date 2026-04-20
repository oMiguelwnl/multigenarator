"""Core job orchestration contracts for Phase 1."""

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SupportedLanguage(str, Enum):
    PT = "pt"
    ES = "es"
    EN = "en"
    FR = "fr"
    DE = "de"
    RU = "ru"
    NL = "nl"


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
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=2, ge=1)


class GenerationRequest(BaseModel):
    language: SupportedLanguage
    source_type: Literal["frequency", "word-list"]
    level: int | None = Field(default=None, ge=1, le=3)
    input_file: Path | None = None
    lexicon_source_file: Path | None = None
    resume_job_id: str | None = None
    overwrite: bool = False
    yes_overwrite: bool = False


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
    "GenerationRequest",
    "JobProgressSnapshot",
    "JobStage",
    "JobStatus",
    "ResumeDiagnostic",
    "RetryPolicy",
    "SupportedLanguage",
]
