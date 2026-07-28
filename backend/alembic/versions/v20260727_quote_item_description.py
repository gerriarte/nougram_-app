"""add description column to quote_items

Los ítems de cotización sólo persistían `custom_service_name`, que además se
autocompleta con etiquetas genéricas ("Por horas 1", "Precio fijo 2"). Sin un
campo de alcance, quien revisa la cotización después no puede saber qué se
cotizó realmente. Se agrega `description` (texto libre, nullable) para guardar
el detalle del ítem y poder mostrarlo en la propuesta al cliente.

Nullable a propósito: las cotizaciones ya existentes no tienen este dato y no
hay forma de derivarlo. La obligatoriedad se aplica en el builder para ítems
nuevos, no a nivel de esquema.

Revision ID: v20260727_item_desc
Revises: v20260709_quote_agent
Create Date: 2026-07-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "v20260727_item_desc"
down_revision: str | None = "v20260709_quote_agent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("quote_items")}
    if "description" not in existing:
        op.add_column("quote_items", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("quote_items")}
    if "description" in existing:
        op.drop_column("quote_items", "description")
