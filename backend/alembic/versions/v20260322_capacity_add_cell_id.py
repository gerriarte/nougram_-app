"""capacity_add_cell_id

Revision ID: v20260322_capacity_cell_id
Revises: v20260322_capacity_tracking
Create Date: 2026-03-22 19:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_capacity_cell_id"
down_revision: str | None = "v20260322_capacity_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("capacity_commitments", sa.Column("cell_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_capacity_commitments_cell_id",
        "capacity_commitments",
        "team_cells",
        ["cell_id"],
        ["id"],
    )
    op.create_index(op.f("ix_capacity_commitments_cell_id"), "capacity_commitments", ["cell_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_capacity_commitments_cell_id"), table_name="capacity_commitments")
    op.drop_constraint("fk_capacity_commitments_cell_id", "capacity_commitments", type_="foreignkey")
    op.drop_column("capacity_commitments", "cell_id")
