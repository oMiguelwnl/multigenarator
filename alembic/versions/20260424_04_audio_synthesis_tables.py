"""Create audio asset tables for phase 4."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260424_04"
down_revision = "20260421_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audio_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("asset_kind", sa.String(length=32), nullable=False),
        sa.Column("display_text", sa.Text(), nullable=False),
        sa.Column("tts_text", sa.Text(), nullable=False),
        sa.Column("ssml_text", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("voice_id", sa.String(length=255), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("format", sa.String(length=64), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("ssml_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "job_id",
            "item_key",
            "asset_kind",
            name="uq_audio_assets_job_id_item_key_asset_kind",
        ),
    )
    op.create_index("ix_audio_assets_job_id", "audio_assets", ["job_id"], unique=False)
    op.create_index("ix_audio_assets_run_key", "audio_assets", ["run_key"], unique=False)
    op.create_index("ix_audio_assets_voice_id", "audio_assets", ["voice_id"], unique=False)
    op.create_index("ix_audio_assets_text_hash", "audio_assets", ["text_hash"], unique=False)
    op.create_index("ix_audio_assets_ssml_hash", "audio_assets", ["ssml_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audio_assets_ssml_hash", table_name="audio_assets")
    op.drop_index("ix_audio_assets_text_hash", table_name="audio_assets")
    op.drop_index("ix_audio_assets_voice_id", table_name="audio_assets")
    op.drop_index("ix_audio_assets_run_key", table_name="audio_assets")
    op.drop_index("ix_audio_assets_job_id", table_name="audio_assets")
    op.drop_table("audio_assets")
