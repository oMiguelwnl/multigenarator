"""Create provider call logs table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_12"
down_revision = "20260505_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_call_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("item_key", sa.String(length=255), nullable=True),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("voice_id", sa.String(length=255), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("fallback_from", sa.String(length=128), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("response_hash", sa.String(length=64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("job_id", "item_key", "operation", "provider", "status"):
        op.create_index(f"ix_provider_call_logs_{column}", "provider_call_logs", [column], unique=False)


def downgrade() -> None:
    for column in ("status", "provider", "operation", "item_key", "job_id"):
        op.drop_index(f"ix_provider_call_logs_{column}", table_name="provider_call_logs")
    op.drop_table("provider_call_logs")
