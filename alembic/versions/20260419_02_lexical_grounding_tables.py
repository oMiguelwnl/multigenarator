"""Create lexical grounding tables for phase 2."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260419_02"
down_revision = "20260418_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lexical_candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("submitted_form", sa.String(length=255), nullable=False),
        sa.Column("normalized_source", sa.String(length=255), nullable=False),
        sa.Column("display_form", sa.String(length=255), nullable=False),
        sa.Column("lemma", sa.String(length=255), nullable=False),
        sa.Column("lemma_key", sa.String(length=255), nullable=False),
        sa.Column("frequency_rank", sa.Integer(), nullable=True),
        sa.Column("frequency_level", sa.Integer(), nullable=True),
        sa.Column("definitions_html", sa.Text(), nullable=True),
        sa.Column("definition_language", sa.String(length=8), nullable=False),
        sa.Column("ipa", sa.String(length=255), nullable=True),
        sa.Column("translation_target_language", sa.String(length=8), nullable=False),
        sa.Column("grounding_status", sa.String(length=32), nullable=False),
        sa.Column("warning_code", sa.String(length=64), nullable=True),
        sa.Column("warning_detail", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_key", name="uq_lexical_candidates_job_id_item_key"),
    )
    op.create_index("ix_lexical_candidates_job_id", "lexical_candidates", ["job_id"], unique=False)
    op.create_index("ix_lexical_candidates_lemma_key", "lexical_candidates", ["lemma_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lexical_candidates_lemma_key", table_name="lexical_candidates")
    op.drop_index("ix_lexical_candidates_job_id", table_name="lexical_candidates")
    op.drop_table("lexical_candidates")
