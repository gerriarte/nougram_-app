"""migrate_money_to_numeric

Revision ID: m20251230
Revises: j1k2l3m4n5o6
Create Date: 2025-12-30 18:50:00.000000

ESTÁNDAR NOUGRAM: Migración Float → Numeric para precisión grado bancario
Migra campos monetarios críticos a Numeric(19,4) y porcentajes a Numeric(10,4)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC


# revision identifiers, used by Alembic.
revision: str = "m20251230"
down_revision: str | None = "j1k2l3m4n5o6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Migrate Float columns to Numeric for bank-grade precision
    ESTÁNDAR NOUGRAM: Precisión financiera grado bancario
    """

    # ============================================
    # FASE 1: Campos monetarios críticos → Numeric(19,4)
    # ============================================

    # Quotes table - campos monetarios
    op.alter_column(
        "quotes",
        "total_internal_cost",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="total_internal_cost::numeric(19,4)",
    )

    op.alter_column(
        "quotes",
        "total_client_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="total_client_price::numeric(19,4)",
    )

    op.alter_column(
        "quotes",
        "revision_cost_per_additional",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="revision_cost_per_additional::numeric(19,4)",
    )

    # QuoteItems table - campos monetarios
    op.alter_column(
        "quote_items",
        "internal_cost",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="internal_cost::numeric(19,4)",
    )

    op.alter_column(
        "quote_items",
        "client_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="client_price::numeric(19,4)",
    )

    op.alter_column(
        "quote_items",
        "fixed_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="fixed_price::numeric(19,4)",
    )

    # QuoteExpenses table - campos monetarios
    op.alter_column(
        "quote_expenses",
        "cost",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="cost::numeric(19,4)",
    )

    op.alter_column(
        "quote_expenses",
        "client_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        postgresql_using="client_price::numeric(19,4)",
    )

    # ============================================
    # FASE 2: Porcentajes/márgenes → Numeric(10,4)
    # ============================================

    # Quotes table - porcentajes
    op.alter_column(
        "quotes",
        "margin_percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        postgresql_using="margin_percentage::numeric(10,4)",
    )

    op.alter_column(
        "quotes",
        "target_margin_percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        postgresql_using="target_margin_percentage::numeric(10,4)",
    )

    # QuoteItems table - porcentajes
    op.alter_column(
        "quote_items",
        "margin_percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        postgresql_using="margin_percentage::numeric(10,4)",
    )

    # QuoteExpenses table - porcentajes
    op.alter_column(
        "quote_expenses",
        "markup_percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        postgresql_using="markup_percentage::numeric(10,4)",
    )

    # ============================================
    # FASE 3: Campos adicionales monetarios y porcentajes
    # ============================================

    # CostFixed table - campos monetarios
    op.alter_column(
        "costs_fixed",
        "amount_monthly",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="amount_monthly::numeric(19,4)",
    )

    # TeamMember table - campos monetarios y porcentajes
    op.alter_column(
        "team_members",
        "salary_monthly_brute",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="salary_monthly_brute::numeric(19,4)",
    )

    op.alter_column(
        "team_members",
        "non_billable_hours_percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="non_billable_hours_percentage::numeric(10,4)",
    )

    # Service table - campos monetarios y porcentajes
    op.alter_column(
        "services",
        "default_margin_target",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="default_margin_target::numeric(10,4)",
    )

    op.alter_column(
        "services",
        "fixed_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        nullable=True,
        postgresql_using="fixed_price::numeric(19,4)",
    )

    op.alter_column(
        "services",
        "recurring_price",
        type_=NUMERIC(precision=19, scale=4),
        existing_type=sa.Float(),
        nullable=True,
        postgresql_using="recurring_price::numeric(19,4)",
    )

    # Tax table - porcentajes
    op.alter_column(
        "taxes",
        "percentage",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="percentage::numeric(10,4)",
    )

    # QuoteItems table - campos adicionales (horas y cantidad)
    op.alter_column(
        "quote_items",
        "estimated_hours",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=True,
        postgresql_using="estimated_hours::numeric(10,4)",
    )

    op.alter_column(
        "quote_items",
        "quantity",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="quantity::numeric(10,4)",
    )

    # QuoteExpenses table - cantidad
    op.alter_column(
        "quote_expenses",
        "quantity",
        type_=NUMERIC(precision=10, scale=4),
        existing_type=sa.Float(),
        nullable=False,
        postgresql_using="quantity::numeric(10,4)",
    )


def downgrade() -> None:
    """
    Revert Numeric columns back to Float (only if necessary)
    WARNING: This may cause precision loss
    """

    # Revert porcentajes
    op.alter_column(
        "quote_expenses",
        "markup_percentage",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=10, scale=4),
    )

    op.alter_column(
        "quote_items",
        "margin_percentage",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=10, scale=4),
    )

    op.alter_column(
        "quotes",
        "target_margin_percentage",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=10, scale=4),
    )

    op.alter_column(
        "quotes",
        "margin_percentage",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=10, scale=4),
    )

    # Revert campos monetarios
    op.alter_column(
        "quote_expenses",
        "client_price",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )

    op.alter_column(
        "quote_expenses", "cost", type_=sa.Float(), existing_type=NUMERIC(precision=19, scale=4)
    )

    op.alter_column(
        "quote_items", "fixed_price", type_=sa.Float(), existing_type=NUMERIC(precision=19, scale=4)
    )

    op.alter_column(
        "quote_items",
        "client_price",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )

    op.alter_column(
        "quote_items",
        "internal_cost",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )

    op.alter_column(
        "quotes",
        "revision_cost_per_additional",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )

    op.alter_column(
        "quotes",
        "total_client_price",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )

    op.alter_column(
        "quotes",
        "total_internal_cost",
        type_=sa.Float(),
        existing_type=NUMERIC(precision=19, scale=4),
    )
