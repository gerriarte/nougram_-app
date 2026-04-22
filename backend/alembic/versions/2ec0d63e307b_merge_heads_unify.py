"""merge_heads_unify

Revision ID: 2ec0d63e307b
Revises: m20251230, q2r3s4t5u6v7
Create Date: 2026-02-14 15:28:28.417998

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2ec0d63e307b"
down_revision: str | None = ("m20251230", "q2r3s4t5u6v7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
