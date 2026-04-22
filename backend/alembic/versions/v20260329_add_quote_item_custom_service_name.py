"""add_quote_item_custom_service_name

Revision ID: v20260329_quote_item_name
Revises: v20260322_billing_requests
Create Date: 2026-03-29 18:35:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "v20260329_quote_item_name"
down_revision: str | None = "v20260322_billing_requests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE quote_items ADD COLUMN IF NOT EXISTS custom_service_name VARCHAR")


def downgrade() -> None:
    op.execute("ALTER TABLE quote_items DROP COLUMN IF EXISTS custom_service_name")
