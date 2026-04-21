"""Create text quality tables for phase 3."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260421_03"
down_revision = "20260419_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "text_quality_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "lexical_candidate_id",
            sa.String(length=36),
            sa.ForeignKey("lexical_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=True),
        sa.Column("translation_text", sa.Text(), nullable=True),
        sa.Column("generation_status", sa.String(length=32), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("repair_attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("confidence_label", sa.String(length=32), nullable=False),
        sa.Column("validation_flags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("sentence_provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("translation_provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_key", name="uq_text_quality_records_job_id_item_key"),
        sa.UniqueConstraint("lexical_candidate_id", name="uq_text_quality_records_lexical_candidate_id"),
    )
    op.create_index("ix_text_quality_records_job_id", "text_quality_records", ["job_id"], unique=False)
    op.create_index(
        "ix_text_quality_records_lexical_candidate_id",
        "text_quality_records",
        ["lexical_candidate_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_text_quality_records_lexical_candidate_id", table_name="text_quality_records")
    op.drop_index("ix_text_quality_records_job_id", table_name="text_quality_records")
    op.drop_table("text_quality_records")
