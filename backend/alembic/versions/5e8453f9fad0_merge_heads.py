"""merge_heads

Revision ID: 5e8453f9fad0
Revises: 8f0817455976, e5f6a7b8c9d0, j1k2l3m4n5o6
Create Date: 2025-12-29 14:54:52.006014

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5e8453f9fad0"
down_revision: str | None = ("8f0817455976", "e5f6a7b8c9d0", "j1k2l3m4n5o6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
