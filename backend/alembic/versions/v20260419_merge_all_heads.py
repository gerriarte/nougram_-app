"""merge_all_heads

Revision ID: v20260419_merge_all_heads
Revises: r20251110_user_password, v20260304_proposals, v20260415_team_apply_social
Create Date: 2026-04-19 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "v20260419_merge_all_heads"
down_revision: str | None = (
    "r20251110_user_password",
    "v20260304_proposals",
    "v20260415_team_apply_social",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
