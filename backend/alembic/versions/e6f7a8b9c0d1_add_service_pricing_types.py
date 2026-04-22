"""add_service_pricing_types

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2025-12-27 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add pricing type fields to services, team_members, and quote_items tables (Sprint 14)

    Steps:
    1. Add pricing_type fields to services (nullable first, then set default)
    2. Add fixed_price, is_recurring, billing_frequency, recurring_price to services
    3. Add non_billable_hours_percentage to team_members (default=0.0)
    4. Add pricing_type, fixed_price, quantity to quote_items (nullable)
    5. Migrate existing services: pricing_type = "hourly"
    6. Make pricing_type NOT NULL in services
    """
    # Step 1: Add pricing_type to services (nullable first)
    op.add_column("services", sa.Column("pricing_type", sa.String(), nullable=True))

    # Step 2: Add other pricing fields to services
    op.add_column("services", sa.Column("fixed_price", sa.Float(), nullable=True))
    op.add_column(
        "services", sa.Column("is_recurring", sa.Boolean(), nullable=True, server_default="false")
    )
    op.add_column("services", sa.Column("billing_frequency", sa.String(), nullable=True))
    op.add_column("services", sa.Column("recurring_price", sa.Float(), nullable=True))

    # Step 3: Add non_billable_hours_percentage to team_members
    op.add_column(
        "team_members",
        sa.Column("non_billable_hours_percentage", sa.Float(), nullable=True, server_default="0.0"),
    )

    # Step 4: Add pricing fields to quote_items
    op.add_column("quote_items", sa.Column("pricing_type", sa.String(), nullable=True))
    op.add_column("quote_items", sa.Column("fixed_price", sa.Float(), nullable=True))
    op.add_column(
        "quote_items", sa.Column("quantity", sa.Float(), nullable=True, server_default="1.0")
    )

    # Step 5: Migrate existing services: set pricing_type = "hourly" for all existing services
    op.execute(
        sa.text("""
        UPDATE services 
        SET pricing_type = 'hourly'
        WHERE pricing_type IS NULL
    """)
    )

    # Step 6: Make pricing_type NOT NULL in services
    op.alter_column(
        "services",
        "pricing_type",
        existing_type=sa.String(),
        nullable=False,
        server_default="hourly",
    )

    # Step 7: Set default for non_billable_hours_percentage in team_members
    op.execute(
        sa.text("""
        UPDATE team_members 
        SET non_billable_hours_percentage = 0.0
        WHERE non_billable_hours_percentage IS NULL
    """)
    )
    op.alter_column(
        "team_members",
        "non_billable_hours_percentage",
        existing_type=sa.Float(),
        nullable=False,
        server_default="0.0",
    )

    # Step 8: Set default for quantity in quote_items
    op.execute(
        sa.text("""
        UPDATE quote_items 
        SET quantity = 1.0
        WHERE quantity IS NULL
    """)
    )
    op.alter_column(
        "quote_items", "quantity", existing_type=sa.Float(), nullable=False, server_default="1.0"
    )


def downgrade() -> None:
    """
    Remove pricing type fields from services, team_members, and quote_items
    """
    # Remove fields from quote_items
    op.drop_column("quote_items", "quantity")
    op.drop_column("quote_items", "fixed_price")
    op.drop_column("quote_items", "pricing_type")

    # Remove fields from team_members
    op.drop_column("team_members", "non_billable_hours_percentage")

    # Remove fields from services
    op.drop_column("services", "recurring_price")
    op.drop_column("services", "billing_frequency")
    op.drop_column("services", "is_recurring")
    op.drop_column("services", "fixed_price")
    op.drop_column("services", "pricing_type")
