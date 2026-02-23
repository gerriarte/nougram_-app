"""add_legal_finance_templates

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2025-12-27 11:00:00.000000

"""
import json
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: str | None = 'e6f7a8b9c0d1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add Legal/Consultoría and Finanzas/Contabilidad templates (Sprint 14)
    """
    # Templates data for Legal and Finance
    templates_data = [
        {
            'industry_type': 'legal_consultoria',
            'name': 'Legal/Consultoría',
            'description': 'Plantilla para firmas legales y consultoría jurídica con facturación por hito y horas no facturables',
            'icon': 'Scale',
            'color': 'bg-amber-500',
            'suggested_roles': [
                {
                    'name': 'Senior Partner',
                    'monthly_cost': 12000,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 32,
                    'seniority': 'senior',
                    'non_billable_hours_percentage': 0.20  # 20% for admin/compliance
                },
                {
                    'name': 'Asociado',
                    'monthly_cost': 8000,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 36,
                    'seniority': 'middle',
                    'non_billable_hours_percentage': 0.10  # 10% for admin/compliance
                },
                {
                    'name': 'Abogado Junior',
                    'monthly_cost': 5000,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 38,
                    'seniority': 'junior',
                    'non_billable_hours_percentage': 0.05  # 5% for admin/compliance
                },
                {
                    'name': 'Paralegal',
                    'monthly_cost': 3500,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 40,
                    'seniority': 'junior',
                    'non_billable_hours_percentage': 0.0
                }
            ],
            'suggested_services': [
                {
                    'name': 'Revisión de Contrato',
                    'pricing_type': 'fixed',
                    'fixed_price': 500,
                    'default_margin_target': 0.50,
                    'category': 'Legal Services',
                    'description': 'Revisión completa de contrato con análisis de cláusulas'
                },
                {
                    'name': 'Sesión de Asesoría',
                    'pricing_type': 'hourly',
                    'default_margin_target': 0.45,
                    'category': 'Legal Services',
                    'description': 'Sesión de asesoría legal por hora'
                },
                {
                    'name': 'Redacción de Documentos',
                    'pricing_type': 'fixed',
                    'fixed_price': 800,
                    'default_margin_target': 0.50,
                    'category': 'Legal Services',
                    'description': 'Redacción de documentos legales (contratos, acuerdos, etc.)'
                },
                {
                    'name': 'Representación Legal',
                    'pricing_type': 'hourly',
                    'default_margin_target': 0.40,
                    'category': 'Legal Services',
                    'description': 'Representación legal en audiencias y procedimientos'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'Licencias Legales',
                    'amount': 200,
                    'category': 'Software',
                    'description': 'Suscripciones a bases de datos legales (Westlaw, LexisNexis)',
                    'adjust_by_region': False
                },
                {
                    'name': 'Seguro de Responsabilidad',
                    'amount': 500,
                    'category': 'Insurance',
                    'description': 'Seguro de responsabilidad profesional',
                    'adjust_by_region': True
                },
                {
                    'name': 'Herramientas de Gestión',
                    'amount': 150,
                    'category': 'Software',
                    'description': 'Software de gestión de casos y clientes',
                    'adjust_by_region': False
                }
            ]
        },
        {
            'industry_type': 'finanzas_contabilidad',
            'name': 'Finanzas/Contabilidad',
            'description': 'Plantilla para firmas de contabilidad y servicios financieros con servicios recurrentes',
            'icon': 'DollarSign',
            'color': 'bg-emerald-500',
            'suggested_roles': [
                {
                    'name': 'Contador Senior',
                    'monthly_cost': 6000,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 35,
                    'seniority': 'senior',
                    'non_billable_hours_percentage': 0.10
                },
                {
                    'name': 'Contador Middle',
                    'monthly_cost': 4000,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 38,
                    'seniority': 'middle',
                    'non_billable_hours_percentage': 0.05
                },
                {
                    'name': 'Auditor Junior',
                    'monthly_cost': 3500,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 40,
                    'seniority': 'junior',
                    'non_billable_hours_percentage': 0.0
                },
                {
                    'name': 'Asistente Contable',
                    'monthly_cost': 2500,
                    'weekly_hours': 40,
                    'billable_hours_per_week': 40,
                    'seniority': 'junior',
                    'non_billable_hours_percentage': 0.0
                }
            ],
            'suggested_services': [
                {
                    'name': 'Declaración de Impuestos',
                    'pricing_type': 'fixed',
                    'fixed_price': 300,
                    'default_margin_target': 0.40,
                    'category': 'Tax Services',
                    'description': 'Preparación y presentación de declaración de impuestos'
                },
                {
                    'name': 'Retainer Mensual',
                    'pricing_type': 'recurring',
                    'is_recurring': True,
                    'billing_frequency': 'monthly',
                    'recurring_price': 1500,
                    'default_margin_target': 0.35,
                    'category': 'Accounting Services',
                    'description': 'Servicio recurrente mensual de contabilidad'
                },
                {
                    'name': 'Auditoría Financiera',
                    'pricing_type': 'hourly',
                    'default_margin_target': 0.45,
                    'category': 'Audit Services',
                    'description': 'Auditoría financiera por hora'
                },
                {
                    'name': 'Asesoría Fiscal',
                    'pricing_type': 'hourly',
                    'default_margin_target': 0.40,
                    'category': 'Tax Services',
                    'description': 'Asesoría fiscal y tributaria por hora'
                },
                {
                    'name': 'Retainer Anual',
                    'pricing_type': 'recurring',
                    'is_recurring': True,
                    'billing_frequency': 'annual',
                    'recurring_price': 15000,
                    'default_margin_target': 0.35,
                    'category': 'Accounting Services',
                    'description': 'Servicio recurrente anual de contabilidad completa'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'SAP Business One',
                    'amount': 300,
                    'category': 'Software',
                    'description': 'Licencia mensual SAP Business One',
                    'adjust_by_region': False
                },
                {
                    'name': 'QuickBooks Enterprise',
                    'amount': 200,
                    'category': 'Software',
                    'description': 'Licencia mensual QuickBooks Enterprise',
                    'adjust_by_region': False
                },
                {
                    'name': 'Oracle Financials',
                    'amount': 500,
                    'category': 'Software',
                    'description': 'Licencia mensual Oracle Financials',
                    'adjust_by_region': False
                },
                {
                    'name': 'Herramientas de Auditoría',
                    'amount': 150,
                    'category': 'Software',
                    'description': 'Software especializado para auditoría',
                    'adjust_by_region': False
                }
            ]
        }
    ]
    
    # Insert templates using raw SQL for better compatibility
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    
    for template_data in templates_data:
        # Convert to JSON string
        suggested_roles_json = json.dumps(template_data.get('suggested_roles')) if template_data.get('suggested_roles') else None
        suggested_services_json = json.dumps(template_data.get('suggested_services')) if template_data.get('suggested_services') else None
        suggested_costs_json = json.dumps(template_data.get('suggested_fixed_costs')) if template_data.get('suggested_fixed_costs') else None
        
        # Build SQL values as strings to avoid nested f-string issues
        def sql_literal(value: str | None) -> str:
            if not value:
                return "NULL"
            return "'" + value.replace("'", "''") + "'"

        industry_type = template_data['industry_type'].replace("'", "''")
        name = template_data['name'].replace("'", "''")
        description = sql_literal(template_data.get('description'))
        icon = sql_literal(template_data.get('icon'))
        color = sql_literal(template_data.get('color'))
        
        roles_val = (sql_literal(suggested_roles_json) + "::jsonb") if suggested_roles_json else "NULL"
        services_val = (sql_literal(suggested_services_json) + "::jsonb") if suggested_services_json else "NULL"
        costs_val = (sql_literal(suggested_costs_json) + "::jsonb") if suggested_costs_json else "NULL"
        
        # Use op.execute() with properly formatted SQL
        if is_postgres:
            # PostgreSQL with JSONB
            op.execute(
                sa.text(f"""
                    INSERT INTO industry_templates 
                    (industry_type, name, description, suggested_roles, suggested_services, 
                     suggested_fixed_costs, is_active, icon, color, created_at)
                    VALUES 
                    ('{industry_type}', 
                     '{name}', 
                     {description}, 
                     {roles_val}, 
                     {services_val}, 
                     {costs_val}, 
                     true, 
                     {icon}, 
                     {color}, 
                     NOW())
                """)
            )
        else:
            # SQLite or other databases with JSON
            roles_val_sqlite = sql_literal(suggested_roles_json) if suggested_roles_json else "NULL"
            services_val_sqlite = sql_literal(suggested_services_json) if suggested_services_json else "NULL"
            costs_val_sqlite = sql_literal(suggested_costs_json) if suggested_costs_json else "NULL"
            op.execute(
                sa.text(f"""
                    INSERT INTO industry_templates 
                    (industry_type, name, description, suggested_roles, suggested_services, 
                     suggested_fixed_costs, is_active, icon, color, created_at)
                    VALUES 
                    ('{industry_type}', 
                     '{name}', 
                     {description}, 
                     {roles_val_sqlite}, 
                     {services_val_sqlite}, 
                     {costs_val_sqlite}, 
                     1, 
                     {icon}, 
                     {color}, 
                     datetime('now'))
                """)
            )


def downgrade() -> None:
    """
    Remove Legal and Finance templates
    """
    op.execute(sa.text("""
        DELETE FROM industry_templates 
        WHERE industry_type IN ('legal_consultoria', 'finanzas_contabilidad')
    """))






