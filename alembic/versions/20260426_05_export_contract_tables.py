"""Create export contract tables for phase 5."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260426_05"
down_revision = "20260424_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "card_exports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("lemma_key", sa.String(length=255), nullable=False),
        sa.Column("note_guid", sa.String(length=64), nullable=False),
        sa.Column("sort_index", sa.Integer(), nullable=False),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("front_of_card", sa.Text(), nullable=False),
        sa.Column("ipa", sa.String(length=255), nullable=True),
        sa.Column("definitions", sa.Text(), nullable=False),
        sa.Column("example_sentence", sa.Text(), nullable=False),
        sa.Column("translation", sa.Text(), nullable=False),
        sa.Column("word_audio", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("sentence_audio", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("image", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_key", name="uq_card_exports_job_id_item_key"),
    )
    op.create_index("ix_card_exports_job_id", "card_exports", ["job_id"], unique=False)
    op.create_index("ix_card_exports_run_key", "card_exports", ["run_key"], unique=False)
    op.create_index("ix_card_exports_lemma_key", "card_exports", ["lemma_key"], unique=False)
    op.create_index("ix_card_exports_note_guid", "card_exports", ["note_guid"], unique=False)
    op.create_index("ix_card_exports_sort_index", "card_exports", ["sort_index"], unique=False)

    op.create_table(
        "deck_exports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("export_format", sa.String(length=16), nullable=False),
        sa.Column("deck_name", sa.String(length=255), nullable=False),
        sa.Column("output_path", sa.String(length=512), nullable=False),
        sa.Column("card_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "export_format", name="uq_deck_exports_job_id_export_format"),
    )
    op.create_index("ix_deck_exports_job_id", "deck_exports", ["job_id"], unique=False)
    op.create_index("ix_deck_exports_run_key", "deck_exports", ["run_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_deck_exports_run_key", table_name="deck_exports")
    op.drop_index("ix_deck_exports_job_id", table_name="deck_exports")
    op.drop_table("deck_exports")

    op.drop_index("ix_card_exports_sort_index", table_name="card_exports")
    op.drop_index("ix_card_exports_note_guid", table_name="card_exports")
    op.drop_index("ix_card_exports_lemma_key", table_name="card_exports")
    op.drop_index("ix_card_exports_run_key", table_name="card_exports")
    op.drop_index("ix_card_exports_job_id", table_name="card_exports")
    op.drop_table("card_exports")
