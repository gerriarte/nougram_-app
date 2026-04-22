"""add_billing_requests_table

Revision ID: v20260322_billing_requests
Revises: v20260322_capacity_cell_id
Create Date: 2026-03-22 22:45:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_billing_requests"
down_revision: str | None = "v20260322_capacity_cell_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "billing_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=64), nullable=False),
        sa.Column("target_plan", sa.String(length=32), nullable=True),
        sa.Column("target_interval", sa.String(length=16), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_billing_requests_id"), "billing_requests", ["id"], unique=False)
    op.create_index(
        op.f("ix_billing_requests_organization_id"),
        "billing_requests",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_requests_requested_by_user_id"),
        "billing_requests",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_billing_requests_request_type"), "billing_requests", ["request_type"], unique=False
    )
    op.create_index(
        op.f("ix_billing_requests_status"), "billing_requests", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_billing_requests_created_at"), "billing_requests", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_requests_created_at"), table_name="billing_requests")
    op.drop_index(op.f("ix_billing_requests_status"), table_name="billing_requests")
    op.drop_index(op.f("ix_billing_requests_request_type"), table_name="billing_requests")
    op.drop_index(op.f("ix_billing_requests_requested_by_user_id"), table_name="billing_requests")
    op.drop_index(op.f("ix_billing_requests_organization_id"), table_name="billing_requests")
    op.drop_index(op.f("ix_billing_requests_id"), table_name="billing_requests")
    op.drop_table("billing_requests")
