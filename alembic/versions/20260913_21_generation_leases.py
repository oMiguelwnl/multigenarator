"""Add fenced ownership for sequential generation jobs.

Revision ID: 20260913_21
Revises: 20260828_19
"""

import sqlalchemy as sa

from alembic import op

revision = "20260913_21"
down_revision = "20260828_19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generation_leases",
        sa.Column("scope_key", sa.String(80), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("token", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.Column("inflight_item_sha256", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("generation_leases")
