"""add accepted_quote_id to projects (drives dashboard for Won projects)

Revision ID: w20260601_accepted
Revises: v20260517_add_vendors
Create Date: 2026-06-01 16:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "w20260601_accepted"
down_revision: str | None = "v20260517_add_vendors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("accepted_quote_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_projects_accepted_quote", "projects", "quotes",
        ["accepted_quote_id"], ["id"], use_alter=True,
    )


def downgrade() -> None:
    op.drop_constraint("fk_projects_accepted_quote", "projects", type_="foreignkey")
    op.drop_column("projects", "accepted_quote_id")
