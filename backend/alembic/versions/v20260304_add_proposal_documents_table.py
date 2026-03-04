"""add_proposal_documents_table

Revision ID: v20260304_proposals
Revises: v20260304
Create Date: 2026-03-04 18:10:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v20260304_proposals"
down_revision: str | None = "v20260304"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proposal_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("is_locked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposal_documents_id", "proposal_documents", ["id"])
    op.create_index("ix_proposal_documents_project_id", "proposal_documents", ["project_id"])
    op.create_index("ix_proposal_documents_organization_id", "proposal_documents", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_proposal_documents_organization_id", table_name="proposal_documents")
    op.drop_index("ix_proposal_documents_project_id", table_name="proposal_documents")
    op.drop_index("ix_proposal_documents_id", table_name="proposal_documents")
    op.drop_table("proposal_documents")
