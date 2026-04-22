"""add_taxes_support

Revision ID: d7dc269bb824
Revises: 362aa60e787f
Create Date: 2025-01-20 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7dc269bb824"
down_revision: str | None = "362aa60e787f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Check if tables already exist (idempotent migration)
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Create taxes table if it doesn't exist
    if "taxes" not in tables:
        op.create_table(
            "taxes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("percentage", sa.Float(), nullable=False),
            sa.Column("country", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_taxes_id"), "taxes", ["id"], unique=False)
        op.create_index(op.f("ix_taxes_code"), "taxes", ["code"], unique=True)
        op.create_index(op.f("ix_taxes_name"), "taxes", ["name"], unique=False)
        op.create_index(op.f("ix_taxes_country"), "taxes", ["country"], unique=False)

    # Create project_taxes association table if it doesn't exist
    if "project_taxes" not in tables:
        op.create_table(
            "project_taxes",
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("tax_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
            ),
            sa.ForeignKeyConstraint(
                ["tax_id"],
                ["taxes.id"],
            ),
            sa.PrimaryKeyConstraint("project_id", "tax_id"),
        )


def downgrade() -> None:
    # Drop association table first
    op.drop_table("project_taxes")

    # Drop indexes
    op.drop_index(op.f("ix_taxes_country"), table_name="taxes")
    op.drop_index(op.f("ix_taxes_name"), table_name="taxes")
    op.drop_index(op.f("ix_taxes_code"), table_name="taxes")
    op.drop_index(op.f("ix_taxes_id"), table_name="taxes")

    # Drop taxes table
    op.drop_table("taxes")
