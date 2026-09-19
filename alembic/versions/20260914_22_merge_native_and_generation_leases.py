"""Merge authorized native schema and ordinary generation ownership.

Revision ID: 20260914_22
Revises: 20260912_20, 20260913_21
"""

from alembic import op

revision = "20260914_22"
down_revision = ("20260912_20", "20260913_21")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The native branch performs its own authorization before creating tables.
    pass


def downgrade() -> None:
    # Fail before Alembic can drop either branch, including on SQLite where DDL
    # outside an explicit transaction is not rolled back by Alembic.
    from multilang.services.native_migration import require_schema_authorization

    require_schema_authorization(op.get_context().config, op.get_bind())
