"""add_equipment_amortization_table

Revision ID: n20260225
Revises: k2l3m4n5o6p7
Create Date: 2026-02-25 12:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "n20260225"
down_revision: str | None = "k2l3m4n5o6p7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment_amortization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("purchase_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate_at_purchase", sa.Numeric(10, 4), nullable=True),
        sa.Column("useful_life_months", sa.Integer(), nullable=False),
        sa.Column("salvage_value", sa.Numeric(15, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("depreciation_method", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_equipment_amortization_category", "equipment_amortization", ["category"], unique=False)
    op.create_index("ix_equipment_amortization_is_active", "equipment_amortization", ["is_active"], unique=False)
    op.create_index("ix_equipment_amortization_organization_id", "equipment_amortization", ["organization_id"], unique=False)
    op.create_index("ix_equipment_amortization_deleted_at", "equipment_amortization", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_equipment_amortization_deleted_at", table_name="equipment_amortization")
    op.drop_index("ix_equipment_amortization_organization_id", table_name="equipment_amortization")
    op.drop_index("ix_equipment_amortization_is_active", table_name="equipment_amortization")
    op.drop_index("ix_equipment_amortization_category", table_name="equipment_amortization")
    op.drop_table("equipment_amortization")

