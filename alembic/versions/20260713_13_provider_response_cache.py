"""Create provider response cache table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_13"
down_revision = "20260526_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_response_cache",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("normalized_response", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("response_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "provider",
            "model",
            "task_type",
            "language",
            "item_key",
            "prompt_hash",
            "prompt_version",
            name="uq_provider_response_cache_key",
        ),
    )
    for column in ("provider", "task_type", "language", "prompt_version"):
        op.create_index(
            f"ix_provider_response_cache_{column}",
            "provider_response_cache",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ("prompt_version", "language", "task_type", "provider"):
        op.drop_index(
            f"ix_provider_response_cache_{column}",
            table_name="provider_response_cache",
        )
    op.drop_table("provider_response_cache")
