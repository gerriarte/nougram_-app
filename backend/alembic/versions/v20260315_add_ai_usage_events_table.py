"""add_ai_usage_events_table

Revision ID: v20260315_ai_usage
Revises: v20260309_client_links
Create Date: 2026-03-15

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "v20260315_ai_usage"
down_revision: str | Sequence[str] | None = "v20260309_client_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("proposal_id", sa.Integer(), nullable=True),
        sa.Column("feature", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="openai"),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposal_documents.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_events_id", "ai_usage_events", ["id"])
    op.create_index("ix_ai_usage_events_organization_id", "ai_usage_events", ["organization_id"])
    op.create_index("ix_ai_usage_events_project_id", "ai_usage_events", ["project_id"])
    op.create_index("ix_ai_usage_events_proposal_id", "ai_usage_events", ["proposal_id"])
    op.create_index("ix_ai_usage_events_feature", "ai_usage_events", ["feature"])
    op.create_index("ix_ai_usage_events_created_at", "ai_usage_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_events_created_at", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_feature", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_proposal_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_project_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_organization_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_id", table_name="ai_usage_events")
    op.drop_table("ai_usage_events")
