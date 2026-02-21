"""add_industry_templates

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-15 10:00:00.000000

"""
import json
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Use FlexibleJSON approach - JSONB for PostgreSQL, JSON for others
def get_json_type():
    """Get appropriate JSON type for current database"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return JSONB()
    else:
        return JSON()


def upgrade() -> None:
    """
    Add industry_templates table and seed data for 5 templates
    """
    json_type = get_json_type()
    
    # Create industry_templates table
    op.create_table(
        'industry_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('industry_type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('suggested_roles', json_type, nullable=True),
        sa.Column('suggested_services', json_type, nullable=True),
        sa.Column('suggested_fixed_costs', json_type, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('industry_type')
    )
    
    op.create_index(op.f('ix_industry_templates_id'), 'industry_templates', ['id'], unique=False)
    op.create_index(op.f('ix_industry_templates_industry_type'), 'industry_templates', ['industry_type'], unique=True)
    op.create_index(op.f('ix_industry_templates_is_active'), 'industry_templates', ['is_active'], unique=False)
    
    # Seed data for 5 templates
    templates_data = [
        {
            'industry_type': 'branding',
            'name': 'Agencia de Branding',
            'description': 'Plantilla para agencias de branding, diseño gráfico e identidad visual',
            'icon': 'Palette',
            'color': 'bg-purple-500',
            'suggested_roles': [
                {
                    'name': 'Diseñador Gráfico Junior',
                    'monthly_cost': 2000,
                    'weekly_hours': 40,
                    'seniority': 'junior'
                },
                {
                    'name': 'Diseñador Gráfico Middle',
                    'monthly_cost': 3500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Diseñador Gráfico Senior',
                    'monthly_cost': 5500,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'Ejecutivo de Cuentas',
                    'monthly_cost': 4000,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Ilustrador',
                    'monthly_cost': 3000,
                    'weekly_hours': 30,
                    'seniority': 'middle'
                }
            ],
            'suggested_services': [
                {
                    'name': 'Diseño de Identidad Visual',
                    'default_hourly_rate': 120,
                    'category': 'Branding',
                    'description': 'Diseño completo de identidad visual corporativa'
                },
                {
                    'name': 'Packaging Design',
                    'default_hourly_rate': 100,
                    'category': 'Branding',
                    'description': 'Diseño de empaques y envases'
                },
                {
                    'name': 'Brand Strategy',
                    'default_hourly_rate': 150,
                    'category': 'Strategy',
                    'description': 'Estrategia y posicionamiento de marca'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'Adobe Creative Cloud',
                    'amount': 52.99,
                    'category': 'Software',
                    'description': 'Suscripción mensual Adobe CC',
                    'adjust_by_region': False
                },
                {
                    'name': 'Figma Team',
                    'amount': 12,
                    'category': 'Software',
                    'description': 'Suscripción Figma por usuario',
                    'adjust_by_region': False
                }
            ]
        },
        {
            'industry_type': 'web_development',
            'name': 'Desarrollo Web/Software',
            'description': 'Plantilla para agencias de desarrollo web y software',
            'icon': 'Code',
            'color': 'bg-blue-500',
            'suggested_roles': [
                {
                    'name': 'Desarrollador Frontend Junior',
                    'monthly_cost': 2500,
                    'weekly_hours': 40,
                    'seniority': 'junior'
                },
                {
                    'name': 'Desarrollador Frontend Middle',
                    'monthly_cost': 4500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Desarrollador Backend Middle',
                    'monthly_cost': 5000,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Project Manager',
                    'monthly_cost': 5500,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'QA Tester',
                    'monthly_cost': 3500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                }
            ],
            'suggested_services': [
                {
                    'name': 'Landing Page',
                    'default_hourly_rate': 80,
                    'category': 'Development',
                    'description': 'Desarrollo de landing page responsive'
                },
                {
                    'name': 'E-commerce',
                    'default_hourly_rate': 120,
                    'category': 'Development',
                    'description': 'Desarrollo de tienda online'
                },
                {
                    'name': 'API REST',
                    'default_hourly_rate': 100,
                    'category': 'Development',
                    'description': 'Desarrollo de API RESTful'
                },
                {
                    'name': 'Mantenimiento',
                    'default_hourly_rate': 60,
                    'category': 'Support',
                    'description': 'Mantenimiento y soporte técnico'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'GitHub Team',
                    'amount': 4,
                    'category': 'Software',
                    'description': 'Suscripción GitHub por usuario',
                    'adjust_by_region': False
                },
                {
                    'name': 'AWS/Azure Credits',
                    'amount': 100,
                    'category': 'Infrastructure',
                    'description': 'Créditos mensuales cloud',
                    'adjust_by_region': True
                },
                {
                    'name': 'Herramientas de Testing',
                    'amount': 50,
                    'category': 'Software',
                    'description': 'Suscripciones herramientas testing',
                    'adjust_by_region': False
                }
            ]
        },
        {
            'industry_type': 'audiovisual',
            'name': 'Producción Audiovisual',
            'description': 'Plantilla para productoras audiovisuales y estudios de video',
            'icon': 'Video',
            'color': 'bg-red-500',
            'suggested_roles': [
                {
                    'name': 'Editor de Video',
                    'monthly_cost': 3500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Director de Fotografía',
                    'monthly_cost': 6000,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'Productor',
                    'monthly_cost': 5500,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'Motion Graphics Designer',
                    'monthly_cost': 4500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                }
            ],
            'suggested_services': [
                {
                    'name': 'Video Corporativo',
                    'default_hourly_rate': 100,
                    'category': 'Production',
                    'description': 'Producción de video corporativo'
                },
                {
                    'name': 'Post-producción',
                    'default_hourly_rate': 90,
                    'category': 'Post-Production',
                    'description': 'Edición y post-producción de video'
                },
                {
                    'name': 'Motion Graphics',
                    'default_hourly_rate': 110,
                    'category': 'Post-Production',
                    'description': 'Diseño de animaciones y motion graphics'
                },
                {
                    'name': 'Animación',
                    'default_hourly_rate': 130,
                    'category': 'Animation',
                    'description': 'Animación 2D/3D'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'Adobe Creative Suite',
                    'amount': 52.99,
                    'category': 'Software',
                    'description': 'Suscripción Adobe para video',
                    'adjust_by_region': False
                },
                {
                    'name': 'Almacenamiento NAS',
                    'amount': 200,
                    'category': 'Infrastructure',
                    'description': 'Almacenamiento para archivos de video',
                    'adjust_by_region': True
                },
                {
                    'name': 'Licencias de Stock',
                    'amount': 100,
                    'category': 'Content',
                    'description': 'Suscripción stock footage/music',
                    'adjust_by_region': False
                }
            ]
        },
        {
            'industry_type': 'marketing_digital',
            'name': 'Marketing Digital',
            'description': 'Plantilla para agencias de marketing digital y social media',
            'icon': 'TrendingUp',
            'color': 'bg-green-500',
            'suggested_roles': [
                {
                    'name': 'Community Manager',
                    'monthly_cost': 3000,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Especialista Paid Media',
                    'monthly_cost': 4500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'SEO Specialist',
                    'monthly_cost': 4000,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Content Creator',
                    'monthly_cost': 3500,
                    'weekly_hours': 30,
                    'seniority': 'middle'
                }
            ],
            'suggested_services': [
                {
                    'name': 'Gestión Redes Sociales',
                    'default_hourly_rate': 70,
                    'category': 'Social Media',
                    'description': 'Gestión completa de redes sociales'
                },
                {
                    'name': 'Campañas Publicidad',
                    'default_hourly_rate': 90,
                    'category': 'Advertising',
                    'description': 'Gestión de campañas publicitarias online'
                },
                {
                    'name': 'SEO',
                    'default_hourly_rate': 85,
                    'category': 'SEO',
                    'description': 'Optimización para motores de búsqueda'
                },
                {
                    'name': 'Content Marketing',
                    'default_hourly_rate': 75,
                    'category': 'Content',
                    'description': 'Creación de contenido estratégico'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'Herramientas de Analytics',
                    'amount': 150,
                    'category': 'Software',
                    'description': 'Suscripciones herramientas analytics',
                    'adjust_by_region': False
                },
                {
                    'name': 'Plataformas de Publicidad',
                    'amount': 500,
                    'category': 'Advertising',
                    'description': 'Presupuesto para plataformas publicitarias',
                    'adjust_by_region': True
                }
            ]
        },
        {
            'industry_type': 'consultoria_software',
            'name': 'Consultoría de Software',
            'description': 'Plantilla para empresas de consultoría técnica y arquitectura de software',
            'icon': 'Settings',
            'color': 'bg-indigo-500',
            'suggested_roles': [
                {
                    'name': 'Consultor Senior',
                    'monthly_cost': 8000,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'Consultor Middle',
                    'monthly_cost': 5500,
                    'weekly_hours': 40,
                    'seniority': 'middle'
                },
                {
                    'name': 'Arquitecto de Software',
                    'monthly_cost': 9000,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                },
                {
                    'name': 'Tech Lead',
                    'monthly_cost': 7500,
                    'weekly_hours': 40,
                    'seniority': 'senior'
                }
            ],
            'suggested_services': [
                {
                    'name': 'Auditoría Técnica',
                    'default_hourly_rate': 180,
                    'category': 'Consulting',
                    'description': 'Auditoría técnica de sistemas y código'
                },
                {
                    'name': 'Arquitectura de Sistemas',
                    'default_hourly_rate': 200,
                    'category': 'Consulting',
                    'description': 'Diseño de arquitectura de software'
                },
                {
                    'name': 'Consultoría Estratégica',
                    'default_hourly_rate': 220,
                    'category': 'Consulting',
                    'description': 'Consultoría estratégica tecnológica'
                }
            ],
            'suggested_fixed_costs': [
                {
                    'name': 'Herramientas de Análisis',
                    'amount': 200,
                    'category': 'Software',
                    'description': 'Herramientas de análisis y profiling',
                    'adjust_by_region': False
                },
                {
                    'name': 'Licencias de Software',
                    'amount': 150,
                    'category': 'Software',
                    'description': 'Licencias varias de desarrollo',
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
    Remove industry_templates table
    """
    op.drop_index(op.f('ix_industry_templates_is_active'), table_name='industry_templates')
    op.drop_index(op.f('ix_industry_templates_industry_type'), table_name='industry_templates')
    op.drop_index(op.f('ix_industry_templates_id'), table_name='industry_templates')
    op.drop_table('industry_templates')

