"""fix_missing_quote_contingency_columns

Revision ID: v20260318_quote_contingency_fix
Revises: v20260315_ledger
Create Date: 2026-03-18 22:05:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "v20260318_quote_contingency_fix"
down_revision: str | None = "v20260315_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Hotfix for environments with schema drift where this historical
    # contingency migration was not physically applied.
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS contingency_description VARCHAR")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS contingency_type VARCHAR")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS contingency_value NUMERIC(19,4)")


def downgrade() -> None:
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS contingency_value")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS contingency_type")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS contingency_description")

