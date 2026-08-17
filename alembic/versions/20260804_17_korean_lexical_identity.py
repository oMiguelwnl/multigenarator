"""Add typed Korean lexical identity evidence to lexical candidates."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260804_17"
down_revision = "20260804_16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lexical_candidates",
        sa.Column("korean_identity", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lexical_candidates", "korean_identity")
