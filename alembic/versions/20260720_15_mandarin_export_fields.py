"""Add frozen Mandarin orthography fields to card exports."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260720_15"
down_revision = "20260714_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("card_exports", sa.Column("mandarin_word_pinyin", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("mandarin_word_traditional", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("mandarin_sentence_pinyin", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("mandarin_sentence_traditional", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("card_exports", "mandarin_sentence_traditional")
    op.drop_column("card_exports", "mandarin_sentence_pinyin")
    op.drop_column("card_exports", "mandarin_word_traditional")
    op.drop_column("card_exports", "mandarin_word_pinyin")
