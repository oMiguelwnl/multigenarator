"""ORM models for persisted job orchestration state."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from multilang.db.base import Base


def _sha256_check(column: str) -> str:
    stripped = column
    for char in "0123456789abcdef":
        stripped = f"replace({stripped}, '{char}', '')"
    return f"length({column}) = 64 AND length({stripped}) = 0"


def _nullable_sha256_check(column: str) -> str:
    return f"{column} IS NULL OR ({_sha256_check(column)})"


def _audio_transition_check() -> str:
    return " OR ".join(
        f"(from_state = '{from_state}' AND to_state = '{to_state}')"
        for from_state, to_state in (
            ("reserved", "staged"),
            ("reserved", "failed_unknown"),
            ("reserved", "blocked_mismatch"),
            ("staged", "published"),
            ("staged", "failed_unknown"),
            ("published", "finalized"),
            ("published", "failed_unknown"),
        )
    )


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
    korean_phase31_pointer_locator_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_phase31_pointer_content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_phase31_validation_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_phase31_snapshot_manifest_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_phase31_snapshot_root_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_frequency_bundle_locator_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_frequency_bundle_content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_frequency_authority: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    korean_provider_policy_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_provider_policy: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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
    card_exports: Mapped[list["CardExportModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    deck_exports: Mapped[list["DeckExportModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    highlight_import_records: Mapped[list["HighlightImportRecordModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    highlight_import_manifest: Mapped["HighlightImportManifestModel | None"] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )


class ProviderResponseCacheModel(Base):
    """Persisted normalized provider response cache."""

    __tablename__ = "provider_response_cache"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "model",
            "task_type",
            "language",
            "item_key",
            "prompt_hash",
            "prompt_version",
            name="uq_provider_response_cache_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_response: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    response_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ProviderCallLogModel(Base):
    """Persisted privacy-safe telemetry for provider call attempts."""

    __tablename__ = "provider_call_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    item_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback_from: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route_policy_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget_snapshot_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cache_key_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_schema_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class HighlightImportRecordModel(Base):
    """Private normalized highlight text for a generation job."""

    __tablename__ = "highlight_import_records"
    __table_args__ = (
        UniqueConstraint("job_id", "highlight_id", name="uq_highlight_import_records_job_id_highlight_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    import_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    highlight_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_index: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="highlight_import_records")


class HighlightImportManifestModel(Base):
    """Safe hash/count-only highlight import manifest for a generation job."""

    __tablename__ = "highlight_import_manifests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    import_content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    candidate_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="highlight_import_manifest")


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
    stage_authority_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage_input_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage_output_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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
    spoken_form: Mapped[str | None] = mapped_column(String(255), nullable=True)
    translation_target_language: Mapped[str] = mapped_column(String(8), nullable=False)
    grounding_status: Mapped[str] = mapped_column(String(32), nullable=False)
    warning_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    warning_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    korean_identity: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    frequency_bundle_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency_source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_review_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_review_aggregate_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lexical_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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
    candidate_selection_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    adaptive_i_plus_one_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    provider_review_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    text_review_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    provider_sdk_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    voice_profile_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    catalog_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    synthesis_request_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_review_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    audio_review_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    heard_review_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fallback_origin: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rejection_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="audio_assets")


class CardExportModel(Base):
    """Persisted frozen export snapshot for a single job item."""

    __tablename__ = "card_exports"
    __table_args__ = (
        UniqueConstraint("job_id", "item_key", name="uq_card_exports_job_id_item_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    lemma_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    note_guid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sort_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    frequency_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_bundle_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    export_gate_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    front_of_card: Mapped[str] = mapped_column(Text, nullable=False)
    ipa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    definitions: Mapped[str] = mapped_column(Text, nullable=False)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    word_audio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sentence_audio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    image: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    gramatica: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_reading: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_romaji: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentence_furigana: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentence_romaji: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandarin_word_pinyin: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandarin_word_traditional: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandarin_sentence_pinyin: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandarin_sentence_traditional: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="card_exports")


class DeckExportModel(Base):
    """Persisted artifact manifest for produced deck exports."""

    __tablename__ = "deck_exports"
    __table_args__ = (
        UniqueConstraint("job_id", "export_format", name="uq_deck_exports_job_id_export_format"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    export_format: Mapped[str] = mapped_column(String(16), nullable=False)
    deck_name: Mapped[str] = mapped_column(String(255), nullable=False)
    output_path: Mapped[str] = mapped_column(String(512), nullable=False)
    card_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    frequency_bundle_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    export_manifest_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    export_gate_receipt_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[GenerationJob] = relationship(back_populates="deck_exports")


class KoreanGrammarBundleModel(Base):
    """Immutable grammar authority bundle metadata."""

    __tablename__ = "korean_grammar_bundles"
    __table_args__ = (
        UniqueConstraint("bundle_id", name="uq_korean_grammar_bundles_bundle_id"),
        CheckConstraint(_sha256_check("bundle_sha256"), name="ck_korean_grammar_bundles_bundle_sha256"),
        CheckConstraint(_sha256_check("source_sha256"), name="ck_korean_grammar_bundles_source_sha256"),
        CheckConstraint("sequence_count >= 0", name="ck_korean_grammar_bundles_sequence_count"),
        CheckConstraint("status IN ('draft','active','retired')", name="ck_korean_grammar_bundles_status"),
        Index("ix_korean_grammar_bundles_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bundle_id: Mapped[str] = mapped_column(String(160), nullable=False)
    bundle_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sequence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class KoreanGrammarMemberModel(Base):
    """Immutable ordered grammar construction within a bundle."""

    __tablename__ = "korean_grammar_members"
    __table_args__ = (
        UniqueConstraint("bundle_id", "sequence_index", name="uq_korean_grammar_members_bundle_sequence"),
        UniqueConstraint("bundle_id", "construction_id", name="uq_korean_grammar_members_bundle_construction"),
        CheckConstraint("sequence_index >= 1", name="ck_korean_grammar_members_sequence_index"),
        CheckConstraint(_sha256_check("member_sha256"), name="ck_korean_grammar_members_member_sha256"),
        Index("ix_korean_grammar_members_bundle_id", "bundle_id"),
        Index("ix_korean_grammar_members_construction_id", "construction_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bundle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("korean_grammar_bundles.id", ondelete="CASCADE"), nullable=False
    )
    construction_id: Mapped[str] = mapped_column(String(160), nullable=False)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    form: Mapped[str] = mapped_column(String(255), nullable=False)
    function_label: Mapped[str] = mapped_column(String(255), nullable=False)
    register: Mapped[str] = mapped_column(String(64), nullable=False)
    prerequisite_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    member_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PersonalSourceRowModel(Base):
    """Immutable ordered personal input row."""

    __tablename__ = "personal_source_rows"
    __table_args__ = (
        UniqueConstraint("job_id", "source_type", "input_position", name="uq_personal_source_rows_position"),
        UniqueConstraint("job_id", "source_type", "source_row_sha256", name="uq_personal_source_rows_source_row_sha256"),
        CheckConstraint("input_position >= 1", name="ck_personal_source_rows_input_position"),
        CheckConstraint(_sha256_check("source_row_sha256"), name="ck_personal_source_rows_source_row_sha256"),
        Index("ix_personal_source_rows_job_id_item_key", "job_id", "item_key"),
        Index("ix_personal_source_rows_source_type", "source_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    input_position: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_form: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_form: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PersonalSourceDecisionModel(Base):
    """Immutable resolution decision for a personal source row."""

    __tablename__ = "personal_source_decisions"
    __table_args__ = (
        UniqueConstraint("row_id", "decision_revision", name="uq_personal_source_decisions_row_revision"),
        CheckConstraint("decision_revision >= 1", name="ck_personal_source_decisions_revision"),
        CheckConstraint(
            "decision_state IN ('accepted','duplicate','bridge','defer','needs_review','rejected')",
            name="ck_personal_source_decisions_state",
        ),
        CheckConstraint(_nullable_sha256_check("korean_identity_sha256"), name="ck_personal_source_decisions_identity_sha256"),
        Index("ix_personal_source_decisions_row_id", "row_id"),
        Index("ix_personal_source_decisions_state", "decision_state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    row_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("personal_source_rows.id", ondelete="CASCADE"), nullable=False
    )
    decision_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    resolved_lemma: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_pos: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_sense_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_state: Mapped[str] = mapped_column(String(32), nullable=False)
    decision_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    korean_identity_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prerequisite_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class HighlightPrivateExcerptRevisionModel(Base):
    """Dedicated immutable private highlight text revision."""

    __tablename__ = "highlight_private_excerpt_revisions"
    __table_args__ = (
        UniqueConstraint("excerpt_revision_id", name="uq_highlight_private_excerpt_revisions_revision_id"),
        UniqueConstraint(
            "job_id",
            "highlight_id",
            "revision_number",
            name="uq_highlight_private_excerpt_revisions_job_highlight_revision",
        ),
        CheckConstraint("source_index >= 0", name="ck_highlight_private_excerpt_revisions_source_index"),
        CheckConstraint("revision_number >= 1", name="ck_highlight_private_excerpt_revisions_revision_number"),
        CheckConstraint(_sha256_check("import_content_hash"), name="ck_highlight_private_excerpt_revisions_import_hash"),
        CheckConstraint(_sha256_check("source_content_hash"), name="ck_highlight_private_excerpt_revisions_source_hash"),
        Index("ix_highlight_private_excerpt_revisions_job_highlight", "job_id", "highlight_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    excerpt_revision_id: Mapped[str] = mapped_column(String(160), nullable=False)
    highlight_id: Mapped[str] = mapped_column(String(255), nullable=False)
    import_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PrivateContextCapabilityModel(Base):
    """Versioned capability row for bounded private-context disclosure."""

    __tablename__ = "private_context_capabilities"
    __table_args__ = (
        UniqueConstraint("capability_id", name="uq_private_context_capabilities_capability_id"),
        UniqueConstraint("idempotency_key_sha256", name="uq_private_context_capabilities_idempotency_key_sha256"),
        CheckConstraint("target_end > target_start", name="ck_private_context_capabilities_target_span"),
        CheckConstraint("max_context_tokens BETWEEN 1 AND 24", name="ck_private_context_capabilities_token_cap"),
        CheckConstraint("max_context_code_points >= 1", name="ck_private_context_capabilities_code_points"),
        CheckConstraint(
            "max_context_utf8_bytes >= max_context_code_points", name="ck_private_context_capabilities_utf8_bytes"
        ),
        CheckConstraint("max_provider_attempts BETWEEN 1 AND 2", name="ck_private_context_capabilities_attempts"),
        CheckConstraint(
            "idempotency_support IN ('supported','unsupported')",
            name="ck_private_context_capabilities_idempotency_support",
        ),
        CheckConstraint(
            "(idempotency_support = 'supported' AND idempotency_key_sha256 IS NOT NULL) OR "
            "(idempotency_support = 'unsupported' AND idempotency_key_sha256 IS NULL)",
            name="ck_private_context_capabilities_idempotency_key",
        ),
        CheckConstraint(
            "tokenization_rule_id = 'phase33-private-token-v1'", name="ck_private_context_capabilities_token_rule"
        ),
        CheckConstraint(
            "state IN ('pending','disclosing','disclosed','failed_unknown')",
            name="ck_private_context_capabilities_state",
        ),
        CheckConstraint("version >= 0", name="ck_private_context_capabilities_version"),
        CheckConstraint(_sha256_check("excerpt_sha256"), name="ck_private_context_capabilities_excerpt_sha256"),
        CheckConstraint(_sha256_check("target_text_sha256"), name="ck_private_context_capabilities_target_sha256"),
        CheckConstraint(_sha256_check("provider_route_sha256"), name="ck_private_context_capabilities_route_sha256"),
        CheckConstraint(_sha256_check("policy_sha256"), name="ck_private_context_capabilities_policy_sha256"),
        CheckConstraint(_sha256_check("issuer_intent_sha256"), name="ck_private_context_capabilities_issuer_sha256"),
        CheckConstraint(
            _nullable_sha256_check("idempotency_key_sha256"),
            name="ck_private_context_capabilities_idempotency_sha256",
        ),
        Index("ix_private_context_capabilities_job_id", "job_id"),
        Index("ix_private_context_capabilities_item_state", "item_id", "state"),
        Index("ix_private_context_capabilities_cas", "capability_id", "state", "version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    capability_id: Mapped[str] = mapped_column(String(160), nullable=False)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String(160), nullable=False)
    item_id: Mapped[str] = mapped_column(String(160), nullable=False)
    excerpt_revision_id: Mapped[str] = mapped_column(String(160), nullable=False)
    excerpt_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    target_start: Mapped[int] = mapped_column(Integer, nullable=False)
    target_end: Mapped[int] = mapped_column(Integer, nullable=False)
    target_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(160), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    route_id: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_route_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(160), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(160), nullable=False)
    policy_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    tokenization_rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    max_context_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    max_context_code_points: Mapped[int] = mapped_column(Integer, nullable=False)
    max_context_utf8_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_provider_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    max_estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    idempotency_support: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    issuer_id: Mapped[str] = mapped_column(String(160), nullable=False)
    issuer_intent_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PrivateDisclosureAttemptModel(Base):
    """Immutable disclosure state attempt without private context text."""

    __tablename__ = "private_disclosure_attempts"
    __table_args__ = (
        UniqueConstraint("capability_id", "version", name="uq_private_disclosure_attempts_capability_version"),
        CheckConstraint(
            "state IN ('pending','disclosing','disclosed','failed_unknown')",
            name="ck_private_disclosure_attempts_state",
        ),
        CheckConstraint("version >= 0", name="ck_private_disclosure_attempts_version"),
        CheckConstraint(
            "context_token_count IS NULL OR context_token_count BETWEEN 1 AND 24",
            name="ck_private_disclosure_attempts_token_count",
        ),
        CheckConstraint(_nullable_sha256_check("context_sha256"), name="ck_private_disclosure_attempts_context_sha256"),
        Index("ix_private_disclosure_attempts_capability_id", "capability_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    capability_id: Mapped[str] = mapped_column(String(160), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    context_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refusal_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PrivateProcessingReceiptModel(Base):
    """Immutable hash/count receipt for a private provider attempt."""

    __tablename__ = "private_processing_receipts"
    __table_args__ = (
        UniqueConstraint("receipt_id", name="uq_private_processing_receipts_receipt_id"),
        UniqueConstraint("receipt_sha256", name="uq_private_processing_receipts_receipt_sha256"),
        CheckConstraint("context_token_count BETWEEN 1 AND 24", name="ck_private_processing_receipts_context_token_count"),
        CheckConstraint(_sha256_check("receipt_sha256"), name="ck_private_processing_receipts_receipt_sha256"),
        CheckConstraint(_sha256_check("context_sha256"), name="ck_private_processing_receipts_context_sha256"),
        CheckConstraint(_sha256_check("policy_sha256"), name="ck_private_processing_receipts_policy_sha256"),
        Index("ix_private_processing_receipts_capability_id", "capability_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    receipt_id: Mapped[str] = mapped_column(String(160), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(160), nullable=False)
    receipt_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    context_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    context_token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(160), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    route_id: Mapped[str] = mapped_column(String(160), nullable=False)
    policy_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReviewFieldRevisionModel(Base):
    """Immutable generated or edited reviewable field revision."""

    __tablename__ = "review_field_revisions"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "item_id", "field_name", "revision_no", name="uq_review_field_revisions_item_field_revision"
        ),
        CheckConstraint("revision_no >= 1", name="ck_review_field_revisions_revision_no"),
        CheckConstraint(_sha256_check("value_sha256"), name="ck_review_field_revisions_value_sha256"),
        CheckConstraint(_nullable_sha256_check("previous_revision_sha256"), name="ck_review_field_revisions_previous_sha256"),
        Index("ix_review_field_revisions_item_field", "job_id", "item_id", "field_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    value_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_id: Mapped[str] = mapped_column(String(160), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(160), nullable=False)
    route_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    previous_revision_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReviewCurrentPointerModel(Base):
    """Mutable current pointer with an explicit CAS version."""

    __tablename__ = "review_current_pointers"
    __table_args__ = (
        UniqueConstraint("job_id", "item_id", "field_name", name="uq_review_current_pointers_item_field"),
        CheckConstraint("pointer_version >= 0", name="ck_review_current_pointers_version"),
        CheckConstraint("review_status IN ('needs_review','approved','rejected')", name="ck_review_current_pointers_status"),
        Index("ix_review_current_pointers_item_field", "job_id", "item_id", "field_name"),
        Index("ix_review_current_pointers_status", "review_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    pointer_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ReviewDecisionModel(Base):
    """Immutable review decision over a field revision."""

    __tablename__ = "review_decisions"
    __table_args__ = (
        UniqueConstraint("revision_id", "decision_revision", name="uq_review_decisions_revision_decision"),
        CheckConstraint("decision_revision >= 1", name="ck_review_decisions_revision"),
        CheckConstraint("review_status IN ('needs_review','approved','rejected')", name="ck_review_decisions_status"),
        CheckConstraint(_nullable_sha256_check("reviewer_id_sha256"), name="ck_review_decisions_reviewer_sha256"),
        CheckConstraint(_sha256_check("decision_sha256"), name="ck_review_decisions_decision_sha256"),
        Index("ix_review_decisions_revision_id", "revision_id"),
        Index("ix_review_decisions_item_field", "job_id", "item_id", "field_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_field_revisions.id", ondelete="CASCADE"), nullable=False
    )
    decision_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer_id_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReviewAccessEventModel(Base):
    """Content-free immutable review access/audit event."""

    __tablename__ = "review_access_events"
    __table_args__ = (
        UniqueConstraint("actor_id", "request_id", "action", name="uq_review_access_events_stable_identity"),
        CheckConstraint(
            "action IN ('list','inspect','private_display','approve','reject','edit','regenerate')",
            name="ck_review_access_events_action",
        ),
        CheckConstraint("result_hash_count >= 0", name="ck_review_access_events_result_count"),
        CheckConstraint(_sha256_check("command_sha256"), name="ck_review_access_events_command_sha256"),
        CheckConstraint(_sha256_check("result_id_sha256"), name="ck_review_access_events_result_id_sha256"),
        CheckConstraint(_sha256_check("policy_sha256"), name="ck_review_access_events_policy_sha256"),
        CheckConstraint(_sha256_check("snapshot_sha256"), name="ck_review_access_events_snapshot_sha256"),
        Index("ix_review_access_events_actor_request", "actor_id", "request_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    request_id: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    command_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    result_id_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    result_hash_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    policy_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ItemTerminalStatusEventModel(Base):
    """Immutable item terminal status event for denominator accounting."""

    __tablename__ = "item_terminal_status_events"
    __table_args__ = (
        UniqueConstraint("job_id", "item_id", "stage", name="uq_item_terminal_status_events_item_stage"),
        UniqueConstraint("event_sha256", name="uq_item_terminal_status_events_event_sha256"),
        CheckConstraint("terminal_status IN ('accepted','review_required','failed')", name="ck_item_terminal_status_events_status"),
        CheckConstraint(_sha256_check("event_sha256"), name="ck_item_terminal_status_events_event_sha256"),
        Index("ix_item_terminal_status_events_status_job", "terminal_status", "job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    terminal_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ItemProcessingFactModel(Base):
    """Immutable attempt/processed fact independent of terminal status."""

    __tablename__ = "item_processing_facts"
    __table_args__ = (
        UniqueConstraint("job_id", "item_id", "stage", "attempt_count", name="uq_item_processing_facts_attempt"),
        UniqueConstraint("fact_sha256", name="uq_item_processing_facts_fact_sha256"),
        CheckConstraint("attempt_count >= 0", name="ck_item_processing_facts_attempt_count"),
        CheckConstraint(_sha256_check("fact_sha256"), name="ck_item_processing_facts_fact_sha256"),
        Index("ix_item_processing_facts_job_item", "job_id", "item_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GenerationRunDenominatorModel(Base):
    """Immutable run denominator snapshot for status reports."""

    __tablename__ = "generation_run_denominators"
    __table_args__ = (
        UniqueConstraint("job_id", "stage", name="uq_generation_run_denominators_job_stage"),
        CheckConstraint(
            "expected_count >= 0 AND accepted_count >= 0 AND review_required_count >= 0 AND failed_count >= 0",
            name="ck_generation_run_denominators_counts",
        ),
        CheckConstraint(
            "accepted_count + review_required_count + failed_count <= expected_count",
            name="ck_generation_run_denominators_count_sum",
        ),
        CheckConstraint(_sha256_check("denominator_sha256"), name="ck_generation_run_denominators_sha256"),
        Index("ix_generation_run_denominators_job_stage", "job_id", "stage"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    review_required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    denominator_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AudioPublicationReservationModel(Base):
    """Mutable reservation row with explicit publication CAS version."""

    __tablename__ = "audio_publication_reservations"
    __table_args__ = (
        UniqueConstraint("field_revision_id", name="uq_audio_publication_reservations_field_revision"),
        UniqueConstraint("final_path_sha256", name="uq_audio_publication_reservations_final_path_sha256"),
        CheckConstraint(
            "expected_pointer_version >= 0 AND reservation_version >= 0",
            name="ck_audio_publication_reservations_versions",
        ),
        CheckConstraint(
            "state IN ('reserved','staged','published','finalized','failed_unknown','blocked_mismatch')",
            name="ck_audio_publication_reservations_state",
        ),
        CheckConstraint(_sha256_check("request_sha256"), name="ck_audio_publication_reservations_request_sha256"),
        CheckConstraint(_sha256_check("final_path_sha256"), name="ck_audio_publication_reservations_final_path_sha256"),
        CheckConstraint(_sha256_check("authority_sha256"), name="ck_audio_publication_reservations_authority_sha256"),
        CheckConstraint(_sha256_check("root_prestate_sha256"), name="ck_audio_publication_reservations_root_sha256"),
        Index("ix_audio_publication_reservations_item_field", "job_id", "item_id", "field_name"),
        Index("ix_audio_publication_reservations_state_job", "state", "job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    final_path: Mapped[str] = mapped_column(String(512), nullable=False)
    final_path_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    authority_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    root_prestate_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_pointer_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reservation_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AudioPublicationTransitionModel(Base):
    """Immutable reservation state transition event."""

    __tablename__ = "audio_publication_transitions"
    __table_args__ = (
        UniqueConstraint("reservation_id", "next_version", name="uq_audio_publication_transitions_reservation_version"),
        UniqueConstraint("transition_sha256", name="uq_audio_publication_transitions_transition_sha256"),
        CheckConstraint("next_version = expected_version + 1", name="ck_audio_publication_transitions_version_step"),
        CheckConstraint(_audio_transition_check(), name="ck_audio_publication_transitions_allowed_step"),
        CheckConstraint(_sha256_check("transition_sha256"), name="ck_audio_publication_transitions_transition_sha256"),
        Index("ix_audio_publication_transitions_reservation_id", "reservation_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("audio_publication_reservations.id", ondelete="CASCADE"), nullable=False
    )
    from_state: Mapped[str] = mapped_column(String(32), nullable=False)
    to_state: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_version: Mapped[int] = mapped_column(Integer, nullable=False)
    next_version: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AudioRevisionEvidenceModel(Base):
    """Immutable finalized audio evidence; byte hash is intentionally non-unique."""

    __tablename__ = "audio_revision_evidence"
    __table_args__ = (
        UniqueConstraint("reservation_id", "role", name="uq_audio_revision_evidence_reservation_role"),
        UniqueConstraint("evidence_sha256", name="uq_audio_revision_evidence_evidence_sha256"),
        CheckConstraint("byte_length > 0", name="ck_audio_revision_evidence_byte_length"),
        CheckConstraint("reservation_state = 'finalized'", name="ck_audio_revision_evidence_reservation_state"),
        CheckConstraint("review_status = 'approved'", name="ck_audio_revision_evidence_review_status"),
        CheckConstraint(_sha256_check("root_sha256"), name="ck_audio_revision_evidence_root_sha256"),
        CheckConstraint(_sha256_check("final_path_sha256"), name="ck_audio_revision_evidence_final_path_sha256"),
        CheckConstraint(_sha256_check("request_sha256"), name="ck_audio_revision_evidence_request_sha256"),
        CheckConstraint(_sha256_check("artifact_sha256"), name="ck_audio_revision_evidence_artifact_sha256"),
        CheckConstraint(_sha256_check("spoken_text_sha256"), name="ck_audio_revision_evidence_spoken_text_sha256"),
        CheckConstraint(_sha256_check("voice_profile_sha256"), name="ck_audio_revision_evidence_voice_profile_sha256"),
        CheckConstraint(_sha256_check("evidence_sha256"), name="ck_audio_revision_evidence_evidence_sha256"),
        Index("ix_audio_revision_evidence_reservation_id", "reservation_id"),
        Index("ix_audio_revision_evidence_final_path", "final_path_sha256"),
        Index("ix_audio_revision_evidence_artifact_sha256", "artifact_sha256"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("audio_publication_reservations.id", ondelete="CASCADE"), nullable=False
    )
    field_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    root_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    final_path_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    spoken_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    voice_profile_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reservation_state: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
