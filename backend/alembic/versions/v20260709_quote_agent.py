"""quote agent module: conversations, messages, project provenance

Creates the persistence for the "Agente de Cotización por Chat" module:
- agent_conversations: one chat session per tenant user
- agent_messages: individual turns (user/assistant/system/tool)
- projects.source: provenance marker so agent-created quotes are identifiable
  in the follow-up pipeline and for the feedback loop.

Revision ID: v20260709_quote_agent
Revises: v20260704b_user_org_nullable
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "v20260709_quote_agent"
down_revision: str | None = "v20260704b_user_org_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    json_type = sa.dialects.postgresql.JSONB() if is_postgres else sa.JSON()

    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("proposed_snapshot", json_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_conversations_id"), "agent_conversations", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_conversations_organization_id"),
        "agent_conversations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_conversations_user_id"),
        "agent_conversations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_conversations_project_id"),
        "agent_conversations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_conversations_quote_id"),
        "agent_conversations",
        ["quote_id"],
        unique=False,
    )

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("meta", json_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_id"), "agent_messages", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_messages_conversation_id"),
        "agent_messages",
        ["conversation_id"],
        unique=False,
    )

    op.add_column("projects", sa.Column("source", sa.String(), nullable=True))
    op.create_index(op.f("ix_projects_source"), "projects", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_source"), table_name="projects")
    op.drop_column("projects", "source")

    op.drop_index(op.f("ix_agent_messages_conversation_id"), table_name="agent_messages")
    op.drop_index(op.f("ix_agent_messages_id"), table_name="agent_messages")
    op.drop_table("agent_messages")

    op.drop_index(op.f("ix_agent_conversations_quote_id"), table_name="agent_conversations")
    op.drop_index(op.f("ix_agent_conversations_project_id"), table_name="agent_conversations")
    op.drop_index(op.f("ix_agent_conversations_user_id"), table_name="agent_conversations")
    op.drop_index(op.f("ix_agent_conversations_organization_id"), table_name="agent_conversations")
    op.drop_index(op.f("ix_agent_conversations_id"), table_name="agent_conversations")
    op.drop_table("agent_conversations")
