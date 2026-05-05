"""Create highlight import record and manifest tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260505_11"
down_revision = "20260502_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "highlight_import_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_content_hash", sa.String(length=64), nullable=False),
        sa.Column("highlight_id", sa.String(length=255), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_index", sa.Integer(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "highlight_id", name="uq_highlight_import_records_job_id_highlight_id"),
    )
    op.create_index("ix_highlight_import_records_job_id", "highlight_import_records", ["job_id"], unique=False)
    op.create_index("ix_highlight_import_records_import_content_hash", "highlight_import_records", ["import_content_hash"], unique=False)
    op.create_index("ix_highlight_import_records_source_content_hash", "highlight_import_records", ["source_content_hash"], unique=False)

    op.create_table(
        "highlight_import_manifests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_content_hash", sa.String(length=64), nullable=False),
        sa.Column("candidate_keys", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("counts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", name="uq_highlight_import_manifests_job_id"),
    )
    op.create_index("ix_highlight_import_manifests_job_id", "highlight_import_manifests", ["job_id"], unique=True)
    op.create_index("ix_highlight_import_manifests_import_content_hash", "highlight_import_manifests", ["import_content_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_highlight_import_manifests_import_content_hash", table_name="highlight_import_manifests")
    op.drop_index("ix_highlight_import_manifests_job_id", table_name="highlight_import_manifests")
    op.drop_table("highlight_import_manifests")
    op.drop_index("ix_highlight_import_records_source_content_hash", table_name="highlight_import_records")
    op.drop_index("ix_highlight_import_records_import_content_hash", table_name="highlight_import_records")
    op.drop_index("ix_highlight_import_records_job_id", table_name="highlight_import_records")
    op.drop_table("highlight_import_records")
