"""add_multi_tenant_organization_support

Revision ID: a1b2c3d4e5f6
Revises: dae436c985e8
Create Date: 2025-12-12 15:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "dae436c985e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add multi-tenant organization support:
    1. Create organizations table
    2. Create default organization
    3. Add organization_id to all tables (nullable first)
    4. Assign all existing records to default organization
    5. Make organization_id NOT NULL
    6. Create composite indexes
    """

    # Step 1: Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("subscription_plan", sa.String(), nullable=False, server_default="free"),
        sa.Column("subscription_status", sa.String(), nullable=False, server_default="active"),
        sa.Column("settings", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)
    op.create_index(op.f("ix_organizations_name"), "organizations", ["name"], unique=False)
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    # Step 2: Create default organization
    op.execute(
        sa.text("""
        INSERT INTO organizations (id, name, slug, subscription_plan, subscription_status, created_at, updated_at)
        VALUES (1, 'Default Organization', 'default', 'enterprise', 'active', NOW(), NOW())
    """)
    )

    # Step 3: Add organization_id to all tables (nullable first)
    op.add_column("users", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("costs_fixed", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("team_members", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("taxes", sa.Column("organization_id", sa.Integer(), nullable=True))

    # Step 4: Assign all existing records to default organization (organization_id = 1)
    op.execute(sa.text("UPDATE users SET organization_id = 1 WHERE organization_id IS NULL"))
    op.execute(sa.text("UPDATE projects SET organization_id = 1 WHERE organization_id IS NULL"))
    op.execute(sa.text("UPDATE services SET organization_id = 1 WHERE organization_id IS NULL"))
    op.execute(sa.text("UPDATE costs_fixed SET organization_id = 1 WHERE organization_id IS NULL"))
    op.execute(sa.text("UPDATE team_members SET organization_id = 1 WHERE organization_id IS NULL"))
    op.execute(sa.text("UPDATE taxes SET organization_id = 1 WHERE organization_id IS NULL"))

    # Step 5: Make organization_id NOT NULL
    op.alter_column("users", "organization_id", nullable=False)
    op.alter_column("projects", "organization_id", nullable=False)
    op.alter_column("services", "organization_id", nullable=False)
    op.alter_column("costs_fixed", "organization_id", nullable=False)
    op.alter_column("team_members", "organization_id", nullable=False)
    op.alter_column("taxes", "organization_id", nullable=False)

    # Step 6: Create foreign keys
    op.create_foreign_key(
        "fk_users_organization_id", "users", "organizations", ["organization_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_projects_organization_id", "projects", "organizations", ["organization_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_services_organization_id", "services", "organizations", ["organization_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_costs_fixed_organization_id",
        "costs_fixed",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_team_members_organization_id",
        "team_members",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_taxes_organization_id", "taxes", "organizations", ["organization_id"], ["id"]
    )

    # Step 7: Create indexes for organization_id
    op.create_index(op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False)
    op.create_index(
        op.f("ix_projects_organization_id"), "projects", ["organization_id"], unique=False
    )
    op.create_index(
        op.f("ix_services_organization_id"), "services", ["organization_id"], unique=False
    )
    op.create_index(
        op.f("ix_costs_fixed_organization_id"), "costs_fixed", ["organization_id"], unique=False
    )
    op.create_index(
        op.f("ix_team_members_organization_id"), "team_members", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_taxes_organization_id"), "taxes", ["organization_id"], unique=False)

    # Step 8: Create composite indexes for multi-tenant queries
    op.create_index(
        "ix_projects_organization_id_created_at",
        "projects",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_projects_organization_id_id", "projects", ["organization_id", "id"], unique=False
    )
    op.create_index(
        "ix_services_organization_id_created_at",
        "services",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_costs_fixed_organization_id_created_at",
        "costs_fixed",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_team_members_organization_id_created_at",
        "team_members",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_taxes_organization_id_created_at",
        "taxes",
        ["organization_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """
    Reverse multi-tenant changes:
    1. Drop composite indexes
    2. Drop organization_id indexes
    3. Drop foreign keys
    4. Drop organization_id columns
    5. Drop organizations table
    """

    # Drop composite indexes
    op.drop_index("ix_taxes_organization_id_created_at", table_name="taxes")
    op.drop_index("ix_team_members_organization_id_created_at", table_name="team_members")
    op.drop_index("ix_costs_fixed_organization_id_created_at", table_name="costs_fixed")
    op.drop_index("ix_services_organization_id_created_at", table_name="services")
    op.drop_index("ix_projects_organization_id_id", table_name="projects")
    op.drop_index("ix_projects_organization_id_created_at", table_name="projects")

    # Drop organization_id indexes
    op.drop_index(op.f("ix_taxes_organization_id"), table_name="taxes")
    op.drop_index(op.f("ix_team_members_organization_id"), table_name="team_members")
    op.drop_index(op.f("ix_costs_fixed_organization_id"), table_name="costs_fixed")
    op.drop_index(op.f("ix_services_organization_id"), table_name="services")
    op.drop_index(op.f("ix_projects_organization_id"), table_name="projects")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")

    # Drop foreign keys
    op.drop_constraint("fk_taxes_organization_id", "taxes", type_="foreignkey")
    op.drop_constraint("fk_team_members_organization_id", "team_members", type_="foreignkey")
    op.drop_constraint("fk_costs_fixed_organization_id", "costs_fixed", type_="foreignkey")
    op.drop_constraint("fk_services_organization_id", "services", type_="foreignkey")
    op.drop_constraint("fk_projects_organization_id", "projects", type_="foreignkey")
    op.drop_constraint("fk_users_organization_id", "users", type_="foreignkey")

    # Drop organization_id columns
    op.drop_column("taxes", "organization_id")
    op.drop_column("team_members", "organization_id")
    op.drop_column("costs_fixed", "organization_id")
    op.drop_column("services", "organization_id")
    op.drop_column("projects", "organization_id")
    op.drop_column("users", "organization_id")

    # Drop organizations table indexes and table
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_name"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")
