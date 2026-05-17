"""add_vendors_table

Revision ID: v20260517_add_vendors
Revises: v20260419_ensure_social_col
Create Date: 2026-05-17 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "v20260517_add_vendors"
down_revision: str | None = "v20260419_ensure_social_col"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("default_cost", sa.Numeric(precision=19, scale=4), nullable=True),
        sa.Column(
            "default_markup_percentage",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendors_id"), "vendors", ["id"], unique=False)
    op.create_index(op.f("ix_vendors_name"), "vendors", ["name"], unique=False)
    op.create_index(
        op.f("ix_vendors_organization_id"), "vendors", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_vendors_deleted_at"), "vendors", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vendors_deleted_at"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_organization_id"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_name"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_id"), table_name="vendors")
    op.drop_table("vendors")
