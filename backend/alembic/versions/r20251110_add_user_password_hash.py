"""add hashed_password column to users

Revision ID: r20251110_user_password
Revises: r20251109_role_varchar
Create Date: 2025-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = "r20251110_user_password"
down_revision = "r20251109_role_varchar"
branch_labels = None
depends_on = None

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = "Abracolombia"
DEFAULT_EMAIL = "gerriarte@abralatam.com"
DEFAULT_NAME = "Gerri Arte"
DEFAULT_ROLE = "super_admin"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default=""),
    )

    conn = op.get_bind()
    default_hash = _pwd_context.hash(DEFAULT_PASSWORD)
    conn.execute(
        text(
            """
            UPDATE users
            SET hashed_password = :hash
            WHERE hashed_password IS NULL OR hashed_password = ''
            """
        ),
        {"hash": default_hash},
    )

    # Ensure default admin user exists
    result = conn.execute(
        text(
            """
            SELECT id FROM users WHERE lower(email) = :email
            """
        ),
        {"email": DEFAULT_EMAIL.lower()},
    ).fetchone()
    if not result:
        conn.execute(
            text(
                """
                INSERT INTO users (email, full_name, role, hashed_password)
                VALUES (:email, :full_name, :role, :hash)
                """
            ),
            {
                "email": DEFAULT_EMAIL.lower(),
                "full_name": DEFAULT_NAME,
                "role": DEFAULT_ROLE,
                "hash": default_hash,
            },
        )

    op.alter_column("users", "hashed_password", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("users")]
    if "hashed_password" in columns:
        op.drop_column("users", "hashed_password")
