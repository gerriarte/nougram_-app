"""add users.role VARCHAR(32) safely if missing

Revision ID: r20251109_role_varchar
Revises: 48d403df0b4b
Create Date: 2025-11-09
"""

from alembic import op

import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "r20251109_role_varchar"
down_revision = "48d403df0b4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Check if column exists
    col_exists = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'role'
            """
        )
    ).fetchone()
    if not col_exists:
        op.add_column(
            "users",
            sa.Column(
                "role", sa.String(length=32), nullable=True, server_default="product_manager"
            ),
        )
        # Create index if missing
        try:
            op.create_index("ix_users_role", "users", ["role"], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    # Safe drop: check if column exists before attempting to drop
    conn = op.get_bind()
    col_exists = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'role'
            """
        )
    ).fetchone()
    if col_exists:
        try:
            op.drop_index("ix_users_role", table_name="users")
        except Exception:
            pass
        op.drop_column("users", "role")
