"""update_templates_with_project_value

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2025-12-27 15:00:00.000000

"""

import json
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "j1k2l3m4n5o6"
down_revision: str | None = "i0j1k2l3m4n5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Update creative templates (branding, audiovisual) with project_value services (Sprint 16)

    Adds services with pricing_type="project_value" for IP/project-based pricing in creative industries.
    """
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Services to add to Branding template
    branding_project_value_services = [
        {
            "name": "Desarrollo de Propiedad Intelectual (IP)",
            "pricing_type": "project_value",
            "default_margin_target": 0.60,
            "category": "IP Development",
            "description": "Desarrollo de propiedad intelectual completa (identidad, marca, sistema visual) - Precio por valor de proyecto/IP",
        },
        {
            "name": "Re-branding Completo",
            "pricing_type": "project_value",
            "default_margin_target": 0.55,
            "category": "Branding",
            "description": "Proyecto completo de re-branding con nuevo sistema de identidad - Precio por valor de proyecto",
        },
    ]

    # Services to add to Audiovisual template
    audiovisual_project_value_services = [
        {
            "name": "Producción de Propiedad Intelectual Audiovisual",
            "pricing_type": "project_value",
            "default_margin_target": 0.60,
            "category": "IP Production",
            "description": "Producción completa de contenido audiovisual con derechos de propiedad intelectual - Precio por valor de proyecto/IP",
        },
        {
            "name": "Serie/Campaña Completa",
            "pricing_type": "project_value",
            "default_margin_target": 0.55,
            "category": "Production",
            "description": "Producción completa de serie o campaña audiovisual - Precio por valor de proyecto",
        },
    ]

    # Update Branding template
    if is_postgres:
        branding_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        if branding_result:
            branding_row = branding_result.fetchone()
        else:
            branding_row = None
        if branding_row and branding_row[0]:
            current_services = (
                branding_row[0]
                if isinstance(branding_row[0], list)
                else json.loads(branding_row[0])
            )
            # Check if services already exist to avoid duplicates
            existing_names = {s.get("name") for s in current_services if isinstance(s, dict)}
            for service in branding_project_value_services:
                if service["name"] not in existing_names:
                    # Convert old format to new format if needed
                    if "default_hourly_rate" in service:
                        # Skip old format services
                        continue
                    current_services.append(service)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(current_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'branding'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(branding_project_value_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'branding'"
                )
            )

        # Update Audiovisual template
        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        if audiovisual_result:
            audiovisual_row = audiovisual_result.fetchone()
        else:
            audiovisual_row = None
        if audiovisual_row and audiovisual_row[0]:
            current_services = (
                audiovisual_row[0]
                if isinstance(audiovisual_row[0], list)
                else json.loads(audiovisual_row[0])
            )
            existing_names = {s.get("name") for s in current_services if isinstance(s, dict)}
            for service in audiovisual_project_value_services:
                if service["name"] not in existing_names:
                    current_services.append(service)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(current_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'audiovisual'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(audiovisual_project_value_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'audiovisual'"
                )
            )
    else:
        # SQLite
        branding_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        branding_row = branding_result.fetchone()
        if branding_row and branding_row[0]:
            current_services = (
                json.loads(branding_row[0]) if isinstance(branding_row[0], str) else branding_row[0]
            )
            existing_names = {s.get("name") for s in current_services if isinstance(s, dict)}
            for service in branding_project_value_services:
                if service["name"] not in existing_names:
                    current_services.append(service)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(current_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'branding'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(branding_project_value_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'branding'"
                )
            )

        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        audiovisual_row = audiovisual_result.fetchone()
        if audiovisual_row and audiovisual_row[0]:
            current_services = (
                json.loads(audiovisual_row[0])
                if isinstance(audiovisual_row[0], str)
                else audiovisual_row[0]
            )
            existing_names = {s.get("name") for s in current_services if isinstance(s, dict)}
            for service in audiovisual_project_value_services:
                if service["name"] not in existing_names:
                    current_services.append(service)
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(current_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'audiovisual'"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(audiovisual_project_value_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'audiovisual'"
                )
            )


def downgrade() -> None:
    """
    Remove project_value services from creative templates
    Note: This removes services with pricing_type='project_value', but may also remove other services if they have the same name
    """
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Service names to remove
    branding_services_to_remove = [
        "Desarrollo de Propiedad Intelectual (IP)",
        "Re-branding Completo",
    ]

    audiovisual_services_to_remove = [
        "Producción de Propiedad Intelectual Audiovisual",
        "Serie/Campaña Completa",
    ]

    # Remove from Branding template
    if is_postgres:
        branding_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        branding_row = branding_result.fetchone()
        if branding_row and branding_row[0]:
            current_services = (
                branding_row[0]
                if isinstance(branding_row[0], list)
                else json.loads(branding_row[0])
            )
            filtered_services = [
                s
                for s in current_services
                if isinstance(s, dict) and s.get("name") not in branding_services_to_remove
            ]
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(filtered_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'branding'"
                )
            )

        # Remove from Audiovisual template
        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        audiovisual_row = audiovisual_result.fetchone()
        if audiovisual_row and audiovisual_row[0]:
            current_services = (
                audiovisual_row[0]
                if isinstance(audiovisual_row[0], list)
                else json.loads(audiovisual_row[0])
            )
            filtered_services = [
                s
                for s in current_services
                if isinstance(s, dict) and s.get("name") not in audiovisual_services_to_remove
            ]
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(filtered_services).replace(chr(39), chr(39) + chr(39))}'::jsonb WHERE industry_type = 'audiovisual'"
                )
            )
    else:
        # SQLite
        branding_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'branding'"
            )
        )
        branding_row = branding_result.fetchone()
        if branding_row and branding_row[0]:
            current_services = (
                json.loads(branding_row[0]) if isinstance(branding_row[0], str) else branding_row[0]
            )
            filtered_services = [
                s
                for s in current_services
                if isinstance(s, dict) and s.get("name") not in branding_services_to_remove
            ]
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(filtered_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'branding'"
                )
            )

        audiovisual_result = op.execute(
            sa.text(
                "SELECT suggested_services FROM industry_templates WHERE industry_type = 'audiovisual'"
            )
        )
        audiovisual_row = audiovisual_result.fetchone()
        if audiovisual_row and audiovisual_row[0]:
            current_services = (
                json.loads(audiovisual_row[0])
                if isinstance(audiovisual_row[0], str)
                else audiovisual_row[0]
            )
            filtered_services = [
                s
                for s in current_services
                if isinstance(s, dict) and s.get("name") not in audiovisual_services_to_remove
            ]
            op.execute(
                sa.text(
                    f"UPDATE industry_templates SET suggested_services = '{json.dumps(filtered_services).replace(chr(39), chr(39) + chr(39))}' WHERE industry_type = 'audiovisual'"
                )
            )
