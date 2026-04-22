"""add_quote_public_link_fields

Revision ID: q2r3s4t5u6v7
Revises: p1q2r3s4t5u6
Create Date: 2026-02-14 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC


# revision identifiers, used by Alembic.
revision: str = "q2r3s4t5u6v7"
down_revision: str | None = "p1q2r3s4t5u6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add public link and tracking fields to quotes table:
    - sent_at: DateTime when quote was sent to client
    - viewed_count: Number of times client opened the link
    - public_token: Token for public access (unique, indexed)
    """
    op.add_column("quotes", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "quotes", sa.Column("viewed_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("quotes", sa.Column("public_token", sa.String(), nullable=True))

    # Create unique index on public_token
    op.create_index(op.f("ix_quotes_public_token"), "quotes", ["public_token"], unique=True)


def downgrade() -> None:
    """
    Remove public link and tracking fields from quotes table
    """
    op.drop_index(op.f("ix_quotes_public_token"), table_name="quotes")
    op.drop_column("quotes", "public_token")
    op.drop_column("quotes", "viewed_count")
    op.drop_column("quotes", "sent_at")
