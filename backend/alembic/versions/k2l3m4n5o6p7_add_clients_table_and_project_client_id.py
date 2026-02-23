"""add_clients_table_and_project_client_id

Revision ID: k2l3m4n5o6p7
Revises: 2ec0d63e307b
Create Date: 2026-02-14 16:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k2l3m4n5o6p7'
down_revision: str | None = '2ec0d63e307b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create clients table (multi-tenant master catalog)
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('requester_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_clients_organization_id'), 'clients', ['organization_id'], unique=False)

    # 2. Add client_id to projects (nullable FK; keep client_name/client_email for snapshot)
    op.add_column('projects', sa.Column('client_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_projects_client_id_clients',
        'projects',
        'clients',
        ['client_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(op.f('ix_projects_client_id'), 'projects', ['client_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projects_client_id'), table_name='projects')
    op.drop_constraint('fk_projects_client_id_clients', 'projects', type_='foreignkey')
    op.drop_column('projects', 'client_id')

    op.drop_index(op.f('ix_clients_organization_id'), table_name='clients')
    op.drop_table('clients')
