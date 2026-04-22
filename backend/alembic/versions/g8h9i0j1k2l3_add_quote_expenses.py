"""add_quote_expenses

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2025-12-27 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g8h9i0j1k2l3"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add quote_expenses table for third-party costs with markup (Sprint 15)
    """
    op.create_table(
        "quote_expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("markup_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("client_price", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["quote_id"],
            ["quotes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quote_expenses_id"), "quote_expenses", ["id"], unique=False)
    op.create_index(
        op.f("ix_quote_expenses_quote_id"), "quote_expenses", ["quote_id"], unique=False
    )


def downgrade() -> None:
    """
    Remove quote_expenses table
    """
    op.drop_index(op.f("ix_quote_expenses_quote_id"), table_name="quote_expenses")
    op.drop_index(op.f("ix_quote_expenses_id"), table_name="quote_expenses")
    op.drop_table("quote_expenses")
