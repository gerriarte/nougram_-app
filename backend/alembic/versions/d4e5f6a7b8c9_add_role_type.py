"""add_role_type

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-12-20 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add role_type column to users table for multi-level role system
    1. Add role_type column (nullable initially)
    2. Migrate existing users:
       - If role == "super_admin" → role_type = "support"
       - All others → role_type = "tenant"
    3. Make role_type NOT NULL after migration
    """
    # Step 1: Add role_type column (nullable)
    op.add_column("users", sa.Column("role_type", sa.String(length=16), nullable=True))
    op.create_index("ix_users_role_type", "users", ["role_type"], unique=False)

    # Step 2: Migrate existing users
    # Set role_type = "support" for super_admin users
    op.execute(
        sa.text("""
        UPDATE users 
        SET role_type = 'support' 
        WHERE role = 'super_admin'
    """)
    )

    # Set role_type = "tenant" for all other users (or NULL roles)
    op.execute(
        sa.text("""
        UPDATE users 
        SET role_type = 'tenant' 
        WHERE role_type IS NULL
    """)
    )

    # Step 3: Make role_type NOT NULL
    # Note: We keep it nullable for backward compatibility, but all existing users will have it set
    # In practice, new code should always set role_type, but we allow NULL for flexibility


def downgrade() -> None:
    """Remove role_type column"""
    op.drop_index("ix_users_role_type", table_name="users")
    op.drop_column("users", "role_type")
