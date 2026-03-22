"""add_quote_item_cell_assignments

Revision ID: v20260322_quote_item_cells
Revises: v20260322_team_cells
Create Date: 2026-03-22 16:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_quote_item_cells"
down_revision: str | None = "v20260322_team_cells"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quote_item_cell_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quote_item_id", sa.Integer(), nullable=False),
        sa.Column("cell_id", sa.Integer(), nullable=False),
        sa.Column("cell_version_id", sa.Integer(), nullable=False),
        sa.Column("occupancy_percentage", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["quote_item_id"], ["quote_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cell_id"], ["team_cells.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cell_version_id"], ["team_cell_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quote_item_id", name="uq_quote_item_cell_assignments_quote_item"),
    )
    op.create_index(op.f("ix_quote_item_cell_assignments_id"), "quote_item_cell_assignments", ["id"], unique=False)
    op.create_index(op.f("ix_quote_item_cell_assignments_quote_item_id"), "quote_item_cell_assignments", ["quote_item_id"], unique=False)
    op.create_index(op.f("ix_quote_item_cell_assignments_cell_id"), "quote_item_cell_assignments", ["cell_id"], unique=False)
    op.create_index(op.f("ix_quote_item_cell_assignments_cell_version_id"), "quote_item_cell_assignments", ["cell_version_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quote_item_cell_assignments_cell_version_id"), table_name="quote_item_cell_assignments")
    op.drop_index(op.f("ix_quote_item_cell_assignments_cell_id"), table_name="quote_item_cell_assignments")
    op.drop_index(op.f("ix_quote_item_cell_assignments_quote_item_id"), table_name="quote_item_cell_assignments")
    op.drop_index(op.f("ix_quote_item_cell_assignments_id"), table_name="quote_item_cell_assignments")
    op.drop_table("quote_item_cell_assignments")
