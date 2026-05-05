"""Add spoken form to lexical candidates.

Revision ID: 20260502_08
Revises: 20260426_05
Create Date: 2026-05-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260502_08"
down_revision = "20260426_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lexical_candidates", sa.Column("spoken_form", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("lexical_candidates", "spoken_form")
