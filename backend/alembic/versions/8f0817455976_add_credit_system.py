"""add_credit_system

Revision ID: 8f0817455976
Revises: d4e5f6a7b8c9
Create Date: 2025-12-23 17:28:48.343529

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f0817455976"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Create credit_accounts and credit_transactions tables for credit system
    """
    # Create credit_accounts table
    op.create_table(
        "credit_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("credits_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_used_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_used_this_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_per_month", sa.Integer(), nullable=True),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_credits_bonus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manual_credits_last_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_credits_assigned_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["manual_credits_assigned_by"], ["users.id"]),
        sa.UniqueConstraint("organization_id"),
    )

    # Create indexes for credit_accounts
    op.create_index(op.f("ix_credit_accounts_id"), "credit_accounts", ["id"], unique=False)
    op.create_index(
        op.f("ix_credit_accounts_organization_id"),
        "credit_accounts",
        ["organization_id"],
        unique=True,
    )

    # Create credit_transactions table
    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("performed_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
    )

    # Create indexes for credit_transactions
    op.create_index(op.f("ix_credit_transactions_id"), "credit_transactions", ["id"], unique=False)
    op.create_index(
        op.f("ix_credit_transactions_organization_id"),
        "credit_transactions",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credit_transactions_transaction_type"),
        "credit_transactions",
        ["transaction_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credit_transactions_created_at"),
        "credit_transactions",
        ["created_at"],
        unique=False,
    )

    # Composite index for common queries (organization + created_at)
    op.create_index(
        "ix_credit_transactions_org_created_at",
        "credit_transactions",
        ["organization_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop credit system tables"""
    # Drop indexes for credit_transactions
    op.drop_index("ix_credit_transactions_org_created_at", table_name="credit_transactions")
    op.drop_index(op.f("ix_credit_transactions_created_at"), table_name="credit_transactions")
    op.drop_index(op.f("ix_credit_transactions_transaction_type"), table_name="credit_transactions")
    op.drop_index(op.f("ix_credit_transactions_organization_id"), table_name="credit_transactions")
    op.drop_index(op.f("ix_credit_transactions_id"), table_name="credit_transactions")
    op.drop_table("credit_transactions")

    # Drop indexes for credit_accounts
    op.drop_index(op.f("ix_credit_accounts_organization_id"), table_name="credit_accounts")
    op.drop_index(op.f("ix_credit_accounts_id"), table_name="credit_accounts")
    op.drop_table("credit_accounts")
