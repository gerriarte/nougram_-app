"""add_quote_revisions

Revision ID: i0j1k2l3m4n5
Revises: h9i0j1k2l3m4
Create Date: 2025-12-27 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "i0j1k2l3m4n5"
down_revision: str | None = "h9i0j1k2l3m4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add revision fields to quotes table (Sprint 16)
    - revisions_included: Number of included revisions (default: 2)
    - revision_cost_per_additional: Cost per additional revision (optional)
    """
    op.add_column(
        "quotes", sa.Column("revisions_included", sa.Integer(), nullable=False, server_default="2")
    )
    op.add_column("quotes", sa.Column("revision_cost_per_additional", sa.Float(), nullable=True))


def downgrade() -> None:
    """
    Remove revision fields from quotes table
    """
    op.drop_column("quotes", "revision_cost_per_additional")
    op.drop_column("quotes", "revisions_included")
