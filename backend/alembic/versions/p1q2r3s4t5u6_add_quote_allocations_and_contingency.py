"""add_quote_allocations_and_contingency

Revision ID: p1q2r3s4t5u6
Revises: i0j1k2l3m4n5
Create Date: 2026-02-14 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC


# revision identifiers, used by Alembic.
revision: str = "p1q2r3s4t5u6"
down_revision: str | None = (
    "3b000e90aba6"  # Follows add_target_margin_percentage migration (latest in main chain)
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add support for resource allocations and contingency in quotes:
    1. Add client_company to projects table
    2. Add contingency fields to quotes table
    3. Add new fields to quote_items table (service_name, recurring_price, billing_frequency, duration_months, project_value, manual_price)
    4. Create quote_item_allocations table for resource allocations
    """

    # Step 1: Add client_company to projects table
    op.add_column("projects", sa.Column("client_company", sa.String(), nullable=True))

    # Step 2: Add contingency fields to quotes table
    op.add_column("quotes", sa.Column("contingency_description", sa.String(), nullable=True))
    op.add_column("quotes", sa.Column("contingency_type", sa.String(), nullable=True))
    op.add_column(
        "quotes", sa.Column("contingency_value", NUMERIC(precision=19, scale=4), nullable=True)
    )

    # Step 3: Add new fields to quote_items table
    op.add_column("quote_items", sa.Column("service_name", sa.String(), nullable=True))
    op.add_column(
        "quote_items", sa.Column("recurring_price", NUMERIC(precision=19, scale=4), nullable=True)
    )
    op.add_column("quote_items", sa.Column("billing_frequency", sa.String(), nullable=True))
    op.add_column("quote_items", sa.Column("duration_months", sa.Integer(), nullable=True))
    op.add_column(
        "quote_items", sa.Column("project_value", NUMERIC(precision=19, scale=4), nullable=True)
    )
    op.add_column(
        "quote_items", sa.Column("manual_price", NUMERIC(precision=19, scale=4), nullable=True)
    )

    # Step 4: Create quote_item_allocations table
    op.create_table(
        "quote_item_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quote_item_id", sa.Integer(), nullable=False),
        sa.Column("team_member_id", sa.Integer(), nullable=False),
        sa.Column("hours", NUMERIC(precision=10, scale=4), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["quote_item_id"], ["quote_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_member_id"], ["team_members.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        op.f("ix_quote_item_allocations_quote_item_id"),
        "quote_item_allocations",
        ["quote_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quote_item_allocations_team_member_id"),
        "quote_item_allocations",
        ["team_member_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove resource allocations and contingency support:
    1. Drop quote_item_allocations table
    2. Remove new fields from quote_items table
    3. Remove contingency fields from quotes table
    4. Remove client_company from projects table
    """

    # Step 1: Drop quote_item_allocations table
    op.drop_index(
        op.f("ix_quote_item_allocations_team_member_id"), table_name="quote_item_allocations"
    )
    op.drop_index(
        op.f("ix_quote_item_allocations_quote_item_id"), table_name="quote_item_allocations"
    )
    op.drop_table("quote_item_allocations")

    # Step 2: Remove new fields from quote_items table
    op.drop_column("quote_items", "manual_price")
    op.drop_column("quote_items", "project_value")
    op.drop_column("quote_items", "duration_months")
    op.drop_column("quote_items", "billing_frequency")
    op.drop_column("quote_items", "recurring_price")
    op.drop_column("quote_items", "service_name")

    # Step 3: Remove contingency fields from quotes table
    op.drop_column("quotes", "contingency_value")
    op.drop_column("quotes", "contingency_type")
    op.drop_column("quotes", "contingency_description")

    # Step 4: Remove client_company from projects table
    op.drop_column("projects", "client_company")
