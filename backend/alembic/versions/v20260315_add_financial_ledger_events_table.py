"""add_financial_ledger_events_table

Revision ID: v20260315_ledger
Revises: v20260315_ai_usage
Create Date: 2026-03-15

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "v20260315_ledger"
down_revision: str | Sequence[str] | None = "v20260315_ai_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_ledger_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="completed"),
        sa.Column("external_id", sa.String(256), nullable=True),
        sa.Column("reference", sa.String(512), nullable=True),
        sa.Column("metadata_json", sa.String(2048), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_ledger_events_id", "financial_ledger_events", ["id"])
    op.create_index(
        "ix_financial_ledger_events_organization_id", "financial_ledger_events", ["organization_id"]
    )
    op.create_index(
        "ix_financial_ledger_events_event_type", "financial_ledger_events", ["event_type"]
    )
    op.create_index("ix_financial_ledger_events_provider", "financial_ledger_events", ["provider"])
    op.create_index("ix_financial_ledger_events_status", "financial_ledger_events", ["status"])
    op.create_index(
        "ix_financial_ledger_events_external_id", "financial_ledger_events", ["external_id"]
    )
    op.create_index(
        "ix_financial_ledger_events_created_at", "financial_ledger_events", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_financial_ledger_events_created_at", table_name="financial_ledger_events")
    op.drop_index("ix_financial_ledger_events_external_id", table_name="financial_ledger_events")
    op.drop_index("ix_financial_ledger_events_status", table_name="financial_ledger_events")
    op.drop_index("ix_financial_ledger_events_provider", table_name="financial_ledger_events")
    op.drop_index("ix_financial_ledger_events_event_type", table_name="financial_ledger_events")
    op.drop_index(
        "ix_financial_ledger_events_organization_id", table_name="financial_ledger_events"
    )
    op.drop_index("ix_financial_ledger_events_id", table_name="financial_ledger_events")
    op.drop_table("financial_ledger_events")
