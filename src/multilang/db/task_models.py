"""Native durable task schema, provisioned only by explicit migrations."""
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from multilang.db.base import Base


class NativeTask(Base):
    __tablename__ = "native_tasks"
    __table_args__ = (
        UniqueConstraint("owner_id", "idempotency_key", name="uq_native_task_owner_key"),
        CheckConstraint("attempts >= 0 AND max_attempts >= 1 AND attempts <= max_attempts", name="ck_native_task_attempts"),
        CheckConstraint("status IN ('pending','running','completed','failed','cancelled')", name="ck_native_task_status"),
        Index("ix_native_tasks_claim", "status", "available_at", "lease_expires_at"),
        {"info": {"native": True}},
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    available_at: Mapped[float] = mapped_column(Float, nullable=False)
    lease_expires_at: Mapped[float | None] = mapped_column(Float)
    worker_id: Mapped[str | None] = mapped_column(String(128))
    lease_token: Mapped[str | None] = mapped_column(String(36))
    error_code: Mapped[str | None] = mapped_column(String(64))
    result_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)
