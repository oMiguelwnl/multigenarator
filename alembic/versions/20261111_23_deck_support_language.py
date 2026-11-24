"""Persist optional per-deck support language.

Revision ID: 20261111_23
Revises: 20260914_22, 20261111_21a
"""

from alembic import op

revision = "20261111_23"
down_revision = ("20260914_22", "20261111_21a")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing installations at revision 23 already have this column.
    pass


def downgrade() -> None:
    from multilang.services.native_migration import require_schema_authorization

    require_schema_authorization(op.get_context().config, op.get_bind())
