"""add client_price_override column to quote_items

El campo "Precio cliente" del builder escribe `manualPrice`, pero para ítems
`hourly` ese valor no tenía ningún canal hacia el backend: no viajaba ni en el
preview (/quotes/calculate) ni al guardar, así que el override se descartaba en
silencio y el precio se recalculaba siempre como costo × margen objetivo.

Se agrega `client_price_override` para persistirlo. Nullable: cuando es NULL el
precio se sigue derivando del cálculo, que es el comportamiento por defecto.

Revision ID: v20260727b_price_ovr
Revises: v20260727_item_desc
Create Date: 2026-07-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "v20260727b_price_ovr"
down_revision: str | None = "v20260727_item_desc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("quote_items")}
    if "client_price_override" not in existing:
        op.add_column(
            "quote_items",
            sa.Column("client_price_override", sa.Numeric(precision=19, scale=4), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns("quote_items")}
    if "client_price_override" in existing:
        op.drop_column("quote_items", "client_price_override")
