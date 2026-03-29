"""add_quote_deletion_controls

Revision ID: v20260329_quote_delete_controls
Revises: v20260329_quote_item_name
Create Date: 2026-03-29 19:30:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "v20260329_quote_delete_controls"
down_revision: str | None = "v20260329_quote_item_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS is_active INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS deletion_requested_by_id INTEGER REFERENCES users(id)")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS deletion_request_reason VARCHAR")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quotes_is_active ON quotes (is_active)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_quotes_is_active")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS deletion_request_reason")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS deletion_requested_by_id")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS deletion_requested_at")
    op.execute("ALTER TABLE quotes DROP COLUMN IF EXISTS is_active")
