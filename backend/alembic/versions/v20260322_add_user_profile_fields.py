"""add_user_profile_fields

Revision ID: v20260322_user_profile
Revises: v20260318_quote_contingency_fix
Create Date: 2026-03-22 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_user_profile"
down_revision: str | None = "v20260318_quote_contingency_fix"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("job_title", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("specialty", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=1000), nullable=True))
    op.add_column("users", sa.Column("linkedin_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("portfolio_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("instagram_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("behance_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("language", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "language")
    op.drop_column("users", "timezone")
    op.drop_column("users", "behance_url")
    op.drop_column("users", "instagram_url")
    op.drop_column("users", "portfolio_url")
    op.drop_column("users", "linkedin_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "specialty")
    op.drop_column("users", "job_title")
