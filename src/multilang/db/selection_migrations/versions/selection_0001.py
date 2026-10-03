"""Preserve multilingual selections without activating generation datasets."""

import sqlalchemy as sa

from alembic import op

revision = "selection_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vocabulary_selection_snapshots",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("total_records", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "vocabulary_selection_units",
        sa.Column(
            "snapshot_id",
            sa.String(64),
            sa.ForeignKey("vocabulary_selection_snapshots.id"),
            primary_key=True,
        ),
        sa.Column("record_id", sa.String(64), primary_key=True),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_selection_language_decision",
        "vocabulary_selection_units",
        ["snapshot_id", "language", "decision"],
    )


def downgrade():
    raise RuntimeError("Selection archive removal requires a separate explicit retention operation")
