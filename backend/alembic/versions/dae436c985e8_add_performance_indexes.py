"""add_performance_indexes

Revision ID: dae436c985e8
Revises: r20251110_user_password
Create Date: 2025-12-12 12:27:24.442136

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dae436c985e8"
down_revision: str | None = "r20251110_user_password"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Helper function to create index if it doesn't exist
    def create_index_if_not_exists(
        index_name: str, table_name: str, columns: list, unique: bool = False
    ):
        from sqlalchemy import inspect

        bind = op.get_bind()
        inspector = inspect(bind)
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=unique)

    # Projects table indexes
    create_index_if_not_exists("ix_projects_status", "projects", ["status"])
    create_index_if_not_exists("ix_projects_created_at", "projects", ["created_at"])
    create_index_if_not_exists(
        "ix_projects_status_created_at", "projects", ["status", "created_at"]
    )

    # Quotes table indexes
    create_index_if_not_exists("ix_quotes_project_id", "quotes", ["project_id"])
    create_index_if_not_exists("ix_quotes_created_at", "quotes", ["created_at"])

    # Quote items table indexes
    create_index_if_not_exists("ix_quote_items_quote_id", "quote_items", ["quote_id"])
    create_index_if_not_exists("ix_quote_items_service_id", "quote_items", ["service_id"])

    # Costs fixed table indexes
    create_index_if_not_exists("ix_costs_fixed_created_at", "costs_fixed", ["created_at"])

    # Services table indexes
    create_index_if_not_exists("ix_services_is_active", "services", ["is_active"])
    create_index_if_not_exists(
        "ix_services_is_active_created_at", "services", ["is_active", "created_at"]
    )

    # Taxes table indexes
    create_index_if_not_exists("ix_taxes_is_active", "taxes", ["is_active"])
    create_index_if_not_exists("ix_taxes_country", "taxes", ["country"])
    create_index_if_not_exists("ix_taxes_code", "taxes", ["code"])
    create_index_if_not_exists("ix_taxes_is_active_country", "taxes", ["is_active", "country"])

    # Team members table indexes
    create_index_if_not_exists("ix_team_members_is_active", "team_members", ["is_active"])
    create_index_if_not_exists("ix_team_members_user_id", "team_members", ["user_id"])
    create_index_if_not_exists(
        "ix_team_members_is_active_created_at", "team_members", ["is_active", "created_at"]
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("ix_team_members_is_active_created_at", table_name="team_members")
    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_team_members_is_active", table_name="team_members")

    op.drop_index("ix_taxes_is_active_country", table_name="taxes")
    op.drop_index("ix_taxes_code", table_name="taxes")
    op.drop_index("ix_taxes_country", table_name="taxes")
    op.drop_index("ix_taxes_is_active", table_name="taxes")

    op.drop_index("ix_services_is_active_created_at", table_name="services")
    op.drop_index("ix_services_is_active", table_name="services")

    op.drop_index("ix_costs_fixed_created_at", table_name="costs_fixed")

    op.drop_index("ix_quote_items_service_id", table_name="quote_items")
    op.drop_index("ix_quote_items_quote_id", table_name="quote_items")

    op.drop_index("ix_quotes_created_at", table_name="quotes")
    op.drop_index("ix_quotes_project_id", table_name="quotes")

    op.drop_index("ix_projects_status_created_at", table_name="projects")
    op.drop_index("ix_projects_created_at", table_name="projects")
    op.drop_index("ix_projects_status", table_name="projects")
