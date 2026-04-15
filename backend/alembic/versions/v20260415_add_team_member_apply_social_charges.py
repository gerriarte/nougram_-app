"""add_team_member_apply_social_charges

Revision ID: v20260415_team_apply_social
Revises: v20260329_quote_delete_controls
Create Date: 2026-04-15 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "v20260415_team_apply_social"
down_revision: str | None = "v20260329_quote_delete_controls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
