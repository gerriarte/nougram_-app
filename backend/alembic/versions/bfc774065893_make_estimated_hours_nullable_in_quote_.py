"""make estimated_hours nullable in quote_items

Revision ID: bfc774065893
Revises: 5e8453f9fad0
Create Date: 2025-12-30 10:13:06.414234

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bfc774065893"
down_revision: str | None = "5e8453f9fad0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Make estimated_hours nullable in quote_items table
    op.alter_column("quote_items", "estimated_hours", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    # Make estimated_hours NOT NULL in quote_items table
    # Note: This might fail if there are rows with null estimated_hours
    op.alter_column("quote_items", "estimated_hours", existing_type=sa.Float(), nullable=False)
