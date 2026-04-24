"""ORM models for persisted job orchestration state."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from multilang.db.base import Base


class GenerationJob(Base):
    """Persisted state for a generation run."""

    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    last_completed_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retrying_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resume_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["GenerationItem"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    lexical_candidates: Mapped[list["LexicalCandidate"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    text_quality_records: Mapped[list["TextQualityRecordModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    audio_assets: Mapped[list["AudioAssetModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class GenerationItem(Base):
    """Persisted state for an individual work item inside a run."""

    __tablename__ = "generation_items"
    __table_args__ = (
        UniqueConstraint("run_key", "item_key", name="uq_generation_items_run_key_item_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_completed_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="items")


class LexicalCandidate(Base):
    """Persisted grounded lexical candidate for a job item."""

    __tablename__ = "lexical_candidates"
    __table_args__ = (
        UniqueConstraint("job_id", "item_key", name="uq_lexical_candidates_job_id_item_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    submitted_form: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_source: Mapped[str] = mapped_column(String(255), nullable=False)
    display_form: Mapped[str] = mapped_column(String(255), nullable=False)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    lemma_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    frequency_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    definitions_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition_language: Mapped[str] = mapped_column(String(8), nullable=False)
    ipa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    translation_target_language: Mapped[str] = mapped_column(String(8), nullable=False)
    grounding_status: Mapped[str] = mapped_column(String(32), nullable=False)
    warning_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    warning_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="lexical_candidates")
    text_quality_record: Mapped["TextQualityRecordModel | None"] = relationship(
        back_populates="lexical_candidate", uselist=False
    )


class TextQualityRecordModel(Base):
    """Persisted sentence-quality record for a single job item."""

    __tablename__ = "text_quality_records"
    __table_args__ = (
        UniqueConstraint("job_id", "item_key", name="uq_text_quality_records_job_id_item_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lexical_candidate_id: Mapped[str] = mapped_column(
        ForeignKey("lexical_candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    repair_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_label: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_flags: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentence_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    translation_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="text_quality_records")
    lexical_candidate: Mapped[LexicalCandidate] = relationship(back_populates="text_quality_record")


class AudioAssetModel(Base):
    """Persisted audio asset for a single job item and asset kind."""

    __tablename__ = "audio_assets"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "item_key",
            "asset_kind",
            name="uq_audio_assets_job_id_item_key_asset_kind",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    tts_text: Mapped[str] = mapped_column(Text, nullable=False)
    ssml_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(32), nullable=False)
    format: Mapped[str] = mapped_column(String(64), nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ssml_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    fallback_used: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="audio_assets")
