"""add_team_cells_module

Revision ID: v20260322_team_cells
Revises: v20260322_user_profile
Create Date: 2026-03-22 15:40:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_team_cells"
down_revision: str | None = "v20260322_user_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "team_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_team_groups_org_name"),
    )
    op.create_index(op.f("ix_team_groups_id"), "team_groups", ["id"], unique=False)
    op.create_index(op.f("ix_team_groups_organization_id"), "team_groups", ["organization_id"], unique=False)

    op.create_table(
        "team_cells",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["team_groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "group_id", "name", name="uq_team_cells_org_group_name"),
    )
    op.create_index(op.f("ix_team_cells_id"), "team_cells", ["id"], unique=False)
    op.create_index(op.f("ix_team_cells_group_id"), "team_cells", ["group_id"], unique=False)
    op.create_index(op.f("ix_team_cells_organization_id"), "team_cells", ["organization_id"], unique=False)

    op.create_table(
        "team_cell_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("cell_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'published'")),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cell_id"], ["team_cells.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cell_id", "version_number", name="uq_team_cell_versions_cell_version"),
    )
    op.create_index(op.f("ix_team_cell_versions_id"), "team_cell_versions", ["id"], unique=False)
    op.create_index(op.f("ix_team_cell_versions_cell_id"), "team_cell_versions", ["cell_id"], unique=False)
    op.create_index(op.f("ix_team_cell_versions_organization_id"), "team_cell_versions", ["organization_id"], unique=False)

    op.create_table(
        "team_cell_member_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("cell_version_id", sa.Integer(), nullable=False),
        sa.Column("team_member_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=False, server_default=sa.text("1.0")),
        sa.Column("role_override", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cell_version_id"], ["team_cell_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["team_member_id"], ["team_members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cell_version_id", "team_member_id", name="uq_team_cell_member_versions_unique_member"),
    )
    op.create_index(op.f("ix_team_cell_member_versions_id"), "team_cell_member_versions", ["id"], unique=False)
    op.create_index(op.f("ix_team_cell_member_versions_cell_version_id"), "team_cell_member_versions", ["cell_version_id"], unique=False)
    op.create_index(op.f("ix_team_cell_member_versions_organization_id"), "team_cell_member_versions", ["organization_id"], unique=False)
    op.create_index(op.f("ix_team_cell_member_versions_team_member_id"), "team_cell_member_versions", ["team_member_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_team_cell_member_versions_team_member_id"), table_name="team_cell_member_versions")
    op.drop_index(op.f("ix_team_cell_member_versions_organization_id"), table_name="team_cell_member_versions")
    op.drop_index(op.f("ix_team_cell_member_versions_cell_version_id"), table_name="team_cell_member_versions")
    op.drop_index(op.f("ix_team_cell_member_versions_id"), table_name="team_cell_member_versions")
    op.drop_table("team_cell_member_versions")

    op.drop_index(op.f("ix_team_cell_versions_organization_id"), table_name="team_cell_versions")
    op.drop_index(op.f("ix_team_cell_versions_cell_id"), table_name="team_cell_versions")
    op.drop_index(op.f("ix_team_cell_versions_id"), table_name="team_cell_versions")
    op.drop_table("team_cell_versions")

    op.drop_index(op.f("ix_team_cells_organization_id"), table_name="team_cells")
    op.drop_index(op.f("ix_team_cells_group_id"), table_name="team_cells")
    op.drop_index(op.f("ix_team_cells_id"), table_name="team_cells")
    op.drop_table("team_cells")

    op.drop_index(op.f("ix_team_groups_organization_id"), table_name="team_groups")
    op.drop_index(op.f("ix_team_groups_id"), table_name="team_groups")
    op.drop_table("team_groups")
