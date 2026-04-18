"""ORM models for persisted job orchestration state."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
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
