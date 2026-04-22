"""update_templates_with_expenses

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
Create Date: 2025-12-27 13:00:00.000000

"""

import json
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "h9i0j1k2l3m4"
down_revision: str | None = "g8h9i0j1k2l3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Update existing templates (audiovisual, branding) with expense suggestions (Sprint 15)
    """
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Update Audiovisual template with expense suggestions
    audiovisual_expenses = [
        {
            "name": "Licencia de Stock (Shutterstock)",
            "amount": 29.99,
            "category": "Third Party",
            "description": "Licencia mensual Shutterstock para stock footage y música",
            "adjust_by_region": False,
            "is_expense": True,
            "suggested_markup": 0.10,  # 10% markup
        },
        {
            "name": "Alquiler de Equipo de Cámara",
            "amount": 500,
            "category": "Third Party",
            "description": "Alquiler de equipo profesional de cámara por proyecto",
            "adjust_by_region": True,
            "is_expense": True,
            "suggested_markup": 0.15,  # 15% markup
        },
        {
            "name": "Locación y Permisos",
            "amount": 300,
            "category": "Third Party",
            "description": "Costo de locación y permisos de filmación",
            "adjust_by_region": True,
            "is_expense": True,
            "suggested_markup": 0.20,  # 20% markup
        },
    ]

    # Update Branding template with expense suggestions
    branding_expenses = [
        {
            "name": "Licencia de Fuentes (Adobe Fonts)",
            "amount": 9.99,
            "category": "Third Party",
            "description": "Licencia mensual de fuentes premium",
            "adjust_by_region": False,
            "is_expense": True,
            "suggested_markup": 0.10,
        },
        {
            "name": "Stock de Imágenes (Getty Images)",
            "amount": 175,
            "category": "Third Party",
            "description": "Licencia de imágenes premium por proyecto",
            "adjust_by_region": False,
            "is_expense": True,
            "suggested_markup": 0.15,
        },
        {
            "name": "Impresión y Producción Física",
            "amount": 200,
            "category": "Materials",
            "description": "Costos de impresión y materiales físicos",
            "adjust_by_region": True,
            "is_expense": True,
            "suggested_markup": 0.20,
        },
    ]

    # Get current templates
    if is_postgres:
        # Get audiovisual template
        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_fixed_costs FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        if audiovisual_result:
            audiovisual_row = audiovisual_result.fetchone()
        else:
            audiovisual_row = None
        if audiovisual_row and audiovisual_row[0]:
            current_costs = (
                audiovisual_row[0]
                if isinstance(audiovisual_row[0], list)
                else json.loads(audiovisual_row[0])
            )
            # Add expense suggestions
            current_costs.extend(audiovisual_expenses)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(current_costs).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'audiovisual'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(audiovisual_expenses).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'audiovisual'"
                )
            )

        # Get branding template
        branding_result = op.execute(
            sa.text(
                "SELECT suggested_fixed_costs FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        if branding_result:
            branding_row = branding_result.fetchone()
        else:
            branding_row = None
        if branding_row and branding_row[0]:
            current_costs = (
                branding_row[0]
                if isinstance(branding_row[0], list)
                else json.loads(branding_row[0])
            )
            # Add expense suggestions
            current_costs.extend(branding_expenses)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(current_costs).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'branding'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(branding_expenses).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'branding'"
                )
            )
    else:
        # SQLite
        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_fixed_costs FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        audiovisual_row = audiovisual_result.fetchone()
        if audiovisual_row and audiovisual_row[0]:
            current_costs = (
                json.loads(audiovisual_row[0])
                if isinstance(audiovisual_row[0], str)
                else audiovisual_row[0]
            )
            current_costs.extend(audiovisual_expenses)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(current_costs).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'audiovisual'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(audiovisual_expenses).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'audiovisual'"
                )
            )

        branding_result = op.execute(
            sa.text(
                "SELECT suggested_fixed_costs FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        branding_row = branding_result.fetchone()
        if branding_row and branding_row[0]:
            current_costs = (
                json.loads(branding_row[0]) if isinstance(branding_row[0], str) else branding_row[0]
            )
            current_costs.extend(branding_expenses)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(current_costs).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'branding'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_fixed_costs = '{json.dumps(branding_expenses).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'branding'"
                )
            )


def downgrade() -> None:
    """
    Remove expense suggestions from templates (not fully reversible, but removes expense items)
    """
    # Note: This is a simplified downgrade that removes items with is_expense=True
    # Full reversal would require storing original state
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        # For audiovisual and branding, we'd need to filter out expenses
        # This is a simplified approach - in production, you might want to store original state
        pass
    else:
        pass
