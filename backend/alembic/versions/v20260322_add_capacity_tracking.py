"""add_capacity_tracking

Revision ID: v20260322_capacity_tracking
Revises: v20260322_quote_item_cells
Create Date: 2026-03-22 18:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260322_capacity_tracking"
down_revision: str | None = "v20260322_quote_item_cells"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "capacity_commitments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("team_member_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hours", sa.Numeric(precision=19, scale=4), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["team_member_id"], ["team_members.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "team_member_id",
            "source_type",
            "source_id",
            "state",
            "period_start",
            "period_end",
            name="uq_capacity_commitments_dedup",
        ),
    )
    op.create_index(
        op.f("ix_capacity_commitments_id"), "capacity_commitments", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_commitments_organization_id"),
        "capacity_commitments",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_commitments_team_member_id"),
        "capacity_commitments",
        ["team_member_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_commitments_source_type"),
        "capacity_commitments",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_commitments_source_id"),
        "capacity_commitments",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_commitments_state"), "capacity_commitments", ["state"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_commitments_period_start"),
        "capacity_commitments",
        ["period_start"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_commitments_period_end"),
        "capacity_commitments",
        ["period_end"],
        unique=False,
    )

    op.create_table(
        "capacity_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_capacity_events_id"), "capacity_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_capacity_events_organization_id"),
        "capacity_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_capacity_events_event_type"), "capacity_events", ["event_type"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_events_source_type"), "capacity_events", ["source_type"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_events_source_id"), "capacity_events", ["source_id"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_events_created_by_id"), "capacity_events", ["created_by_id"], unique=False
    )
    op.create_index(
        op.f("ix_capacity_events_created_at"), "capacity_events", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_capacity_events_created_at"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_created_by_id"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_source_id"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_source_type"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_event_type"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_organization_id"), table_name="capacity_events")
    op.drop_index(op.f("ix_capacity_events_id"), table_name="capacity_events")
    op.drop_table("capacity_events")

    op.drop_index(op.f("ix_capacity_commitments_period_end"), table_name="capacity_commitments")
    op.drop_index(op.f("ix_capacity_commitments_period_start"), table_name="capacity_commitments")
    op.drop_index(op.f("ix_capacity_commitments_state"), table_name="capacity_commitments")
    op.drop_index(op.f("ix_capacity_commitments_source_id"), table_name="capacity_commitments")
    op.drop_index(op.f("ix_capacity_commitments_source_type"), table_name="capacity_commitments")
    op.drop_index(op.f("ix_capacity_commitments_team_member_id"), table_name="capacity_commitments")
    op.drop_index(
        op.f("ix_capacity_commitments_organization_id"), table_name="capacity_commitments"
    )
    op.drop_index(op.f("ix_capacity_commitments_id"), table_name="capacity_commitments")
    op.drop_table("capacity_commitments")
