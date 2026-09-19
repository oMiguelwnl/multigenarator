"""Cross-process ownership of sequential text generation jobs."""

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from multilang.db.base import Base


class GenerationLeaseRecord(Base):
    __tablename__ = "generation_leases"

    scope_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    token: Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)
    inflight_item_sha256: Mapped[str | None] = mapped_column(String(64))
