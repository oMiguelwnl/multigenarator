"""Create job persistence tables for phase 1."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260418_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_fingerprint", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("last_completed_stage", sa.String(length=64), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retrying_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resume_state", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_generation_jobs_run_key", "generation_jobs", ["run_key"], unique=True)

    op.create_table(
        "generation_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_completed_stage", sa.String(length=64), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("run_key", "item_key", name="uq_generation_items_run_key_item_key"),
    )
    op.create_index("ix_generation_items_job_id", "generation_items", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generation_items_job_id", table_name="generation_items")
    op.drop_table("generation_items")
    op.drop_index("ix_generation_jobs_run_key", table_name="generation_jobs")
    op.drop_table("generation_jobs")
