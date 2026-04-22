"""add_invitations

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-12-26 15:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Create invitations table for organization user invitations

    This table tracks invitations sent to users to join organizations:
    - Unique token for accepting invitations
    - Expiration dates
    - Status tracking (pending, accepted, expired)
    - Role assignment upon acceptance
    """
    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_invitations_id", "invitations", ["id"], unique=False)
    op.create_index(
        "ix_invitations_organization_id", "invitations", ["organization_id"], unique=False
    )
    op.create_index("ix_invitations_email", "invitations", ["email"], unique=False)
    op.create_index("ix_invitations_token", "invitations", ["token"], unique=True)
    op.create_index("ix_invitations_expires_at", "invitations", ["expires_at"], unique=False)
    op.create_index("ix_invitations_created_by_id", "invitations", ["created_by_id"], unique=False)

    # Composite index for common queries (organization + email)
    op.create_index(
        "ix_invitations_org_email", "invitations", ["organization_id", "email"], unique=False
    )


def downgrade() -> None:
    """
    Drop invitations table and all indexes
    """
    op.drop_index("ix_invitations_org_email", table_name="invitations")
    op.drop_index("ix_invitations_created_by_id", table_name="invitations")
    op.drop_index("ix_invitations_expires_at", table_name="invitations")
    op.drop_index("ix_invitations_token", table_name="invitations")
    op.drop_index("ix_invitations_email", table_name="invitations")
    op.drop_index("ix_invitations_organization_id", table_name="invitations")
    op.drop_index("ix_invitations_id", table_name="invitations")
    op.drop_table("invitations")
