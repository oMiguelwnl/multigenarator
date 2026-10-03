"""Versioned preparation snapshots, isolated from card-generation state.

A dedicated Alembic history provisions these two tables in the configured DB;
ordinary runtime and native-dataset migrations remain unchanged.
"""

from sqlalchemy import JSON, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SelectionBase(DeclarativeBase):
    pass


class VocabularySelectionSnapshot(SelectionBase):
    __tablename__ = "vocabulary_selection_snapshots"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    total_records: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)


class VocabularySelectionUnit(SelectionBase):
    __tablename__ = "vocabulary_selection_units"
    __table_args__ = (
        Index("ix_selection_language_decision", "snapshot_id", "language", "decision"),
    )
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("vocabulary_selection_snapshots.id"), primary_key=True
    )
    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language: Mapped[str] = mapped_column(String(8))
    decision: Mapped[str] = mapped_column(String(32))
    payload_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
