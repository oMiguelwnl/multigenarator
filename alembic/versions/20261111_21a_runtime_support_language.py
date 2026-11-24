"""Add the per-deck support language on the ordinary runtime branch."""

import sqlalchemy as sa

from alembic import op

revision = "20261111_21a"
down_revision = "20260913_21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adopted create_all databases can already contain the ORM column.
    columns = sa.inspect(op.get_bind()).get_columns("generation_jobs")
    if not any(column["name"] == "support_language" for column in columns):
        op.add_column("generation_jobs", sa.Column("support_language", sa.String(8), nullable=True))


def downgrade() -> None:
    op.drop_column("generation_jobs", "support_language")
