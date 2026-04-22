"""add_soft_delete_support

Revision ID: 48d403df0b4b
Revises: d7dc269bb824
Create Date: 2025-11-08 17:07:15.222875

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "48d403df0b4b"
down_revision: str | None = "d7dc269bb824"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add soft delete fields to projects table
    op.add_column("projects", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("projects", sa.Column("deleted_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_projects_deleted_at"), "projects", ["deleted_at"], unique=False)
    op.create_foreign_key("fk_projects_deleted_by", "projects", "users", ["deleted_by_id"], ["id"])

    # Add soft delete fields to services table
    op.add_column("services", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("services", sa.Column("deleted_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_services_deleted_at"), "services", ["deleted_at"], unique=False)
    op.create_foreign_key("fk_services_deleted_by", "services", "users", ["deleted_by_id"], ["id"])

    # Add soft delete fields to costs_fixed table
    op.add_column("costs_fixed", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("costs_fixed", sa.Column("deleted_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_costs_fixed_deleted_at"), "costs_fixed", ["deleted_at"], unique=False)
    op.create_foreign_key(
        "fk_costs_fixed_deleted_by", "costs_fixed", "users", ["deleted_by_id"], ["id"]
    )

    # Add soft delete fields to taxes table
    op.add_column("taxes", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("taxes", sa.Column("deleted_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_taxes_deleted_at"), "taxes", ["deleted_at"], unique=False)
    op.create_foreign_key("fk_taxes_deleted_by", "taxes", "users", ["deleted_by_id"], ["id"])


def downgrade() -> None:
    # Remove soft delete fields from taxes table
    op.drop_constraint("fk_taxes_deleted_by", "taxes", type_="foreignkey")
    op.drop_index(op.f("ix_taxes_deleted_at"), table_name="taxes")
    op.drop_column("taxes", "deleted_by_id")
    op.drop_column("taxes", "deleted_at")

    # Remove soft delete fields from costs_fixed table
    op.drop_constraint("fk_costs_fixed_deleted_by", "costs_fixed", type_="foreignkey")
    op.drop_index(op.f("ix_costs_fixed_deleted_at"), table_name="costs_fixed")
    op.drop_column("costs_fixed", "deleted_by_id")
    op.drop_column("costs_fixed", "deleted_at")

    # Remove soft delete fields from services table
    op.drop_constraint("fk_services_deleted_by", "services", type_="foreignkey")
    op.drop_index(op.f("ix_services_deleted_at"), table_name="services")
    op.drop_column("services", "deleted_by_id")
    op.drop_column("services", "deleted_at")

    # Remove soft delete fields from projects table
    op.drop_constraint("fk_projects_deleted_by", "projects", type_="foreignkey")
    op.drop_index(op.f("ix_projects_deleted_at"), table_name="projects")
    op.drop_column("projects", "deleted_by_id")
    op.drop_column("projects", "deleted_at")
