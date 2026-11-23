"""Persist optional per-deck support language.

Revision ID: 20261111_23
Revises: 20260914_22
"""

import sqlalchemy as sa

from alembic import op

revision = "20261111_23"
down_revision = "20260914_22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("support_language", sa.String(length=8), nullable=True),
    )


def downgrade() -> None:
    from multilang.services.native_migration import require_schema_authorization

    require_schema_authorization(op.get_context().config, op.get_bind())
    op.drop_column("generation_jobs", "support_language")
