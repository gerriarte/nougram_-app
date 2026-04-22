"""add_target_margin_percentage_to_quotes

Revision ID: 3b000e90aba6
Revises: bfc774065893
Create Date: 2025-12-30 18:06:48.789912

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3b000e90aba6"
down_revision: str | None = "bfc774065893"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add target_margin_percentage column to quotes table
    op.add_column("quotes", sa.Column("target_margin_percentage", sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove target_margin_percentage column from quotes table
    op.drop_column("quotes", "target_margin_percentage")
