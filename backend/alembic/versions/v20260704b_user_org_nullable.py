"""make users.organization_id nullable (support/super_admin role)

The multi-tenant migration (a1b2c3d4e5f6) set users.organization_id to
NOT NULL, but the ORM model declares it nullable=True because support-role
users (super_admin) legitimately have no organization. No later migration
reverted the constraint, so the DB schema drifted from the model: any attempt
to create a user with organization_id=NULL (e.g. the startup super-admin
bootstrap) fails with a NOT NULL violation.

This migration realigns the column with the model. PostgreSQL-only; the test
suite builds its schema from the (already-nullable) model metadata on SQLite.

Revision ID: v20260704b_user_org_nullable
Revises: v20260704_reset_sequences
Create Date: 2026-07-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "v20260704b_user_org_nullable"
down_revision: str | None = "v20260704_reset_sequences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
