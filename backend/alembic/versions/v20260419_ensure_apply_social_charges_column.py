"""ensure_apply_social_charges_column

Revision ID: v20260419_ensure_social_col
Revises: v20260419_merge_all_heads
Create Date: 2026-04-19 18:00:00.000000

Adds apply_social_charges to team_members if it does not already exist.
Idempotent: safe to run even if the column was added by a prior migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "v20260419_ensure_social_col"
down_revision: str | None = "v20260419_merge_all_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'team_members' AND column_name = 'apply_social_charges'"
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "team_members",
            sa.Column(
                "apply_social_charges",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )


def downgrade() -> None:
    op.drop_column("team_members", "apply_social_charges")
