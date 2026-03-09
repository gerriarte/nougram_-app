"""add_proposal_client_links_table

Revision ID: v20260309_client_links
Revises: n20260225, v20260304_proposals
Create Date: 2026-03-09 11:15:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260309_client_links"
down_revision: str | Sequence[str] | None = ("n20260225", "v20260304_proposals")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proposal_client_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("public_token", sa.String(), nullable=False),
        sa.Column("access_code_hash", sa.String(), nullable=True),
        sa.Column("access_code_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="sent"),
        sa.Column("decision_comment", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposal_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proposal_client_links_proposal_id"), "proposal_client_links", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_proposal_client_links_project_id"), "proposal_client_links", ["project_id"], unique=False)
    op.create_index(op.f("ix_proposal_client_links_organization_id"), "proposal_client_links", ["organization_id"], unique=False)
    op.create_index(op.f("ix_proposal_client_links_quote_id"), "proposal_client_links", ["quote_id"], unique=False)
    op.create_index(op.f("ix_proposal_client_links_public_token"), "proposal_client_links", ["public_token"], unique=True)
    op.create_index(op.f("ix_proposal_client_links_access_expires_at"), "proposal_client_links", ["access_expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_proposal_client_links_access_expires_at"), table_name="proposal_client_links")
    op.drop_index(op.f("ix_proposal_client_links_public_token"), table_name="proposal_client_links")
    op.drop_index(op.f("ix_proposal_client_links_quote_id"), table_name="proposal_client_links")
    op.drop_index(op.f("ix_proposal_client_links_organization_id"), table_name="proposal_client_links")
    op.drop_index(op.f("ix_proposal_client_links_project_id"), table_name="proposal_client_links")
    op.drop_index(op.f("ix_proposal_client_links_proposal_id"), table_name="proposal_client_links")
    op.drop_table("proposal_client_links")
