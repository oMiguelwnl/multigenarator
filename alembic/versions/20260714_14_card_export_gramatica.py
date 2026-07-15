"""Add gramatica column to card_exports for structured Latin grammar."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260714_14"
down_revision = "20260713_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "card_exports",
        sa.Column("gramatica", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("card_exports", "gramatica")
