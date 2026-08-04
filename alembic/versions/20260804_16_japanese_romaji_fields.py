"""Add frozen Japanese reading and romaji fields to card exports."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260804_16"
down_revision = "20260720_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("card_exports", sa.Column("word_reading", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("word_romaji", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("sentence_furigana", sa.Text(), nullable=True))
    op.add_column("card_exports", sa.Column("sentence_romaji", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("card_exports", "sentence_romaji")
    op.drop_column("card_exports", "sentence_furigana")
    op.drop_column("card_exports", "word_romaji")
    op.drop_column("card_exports", "word_reading")
