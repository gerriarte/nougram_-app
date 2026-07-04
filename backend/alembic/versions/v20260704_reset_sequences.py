"""reset all serial sequences to max(id)

Fixes fresh-deploy failures on PostgreSQL where seed migrations insert rows with
explicit primary keys (e.g. the multi-tenant migration inserts organizations
with id=1) without advancing the owning sequence. On a brand-new database this
leaves every sequence at its start value, so the first auto-generated INSERT
collides with the seeded row ("duplicate key value violates unique constraint").

This migration realigns every serial sequence in the public schema to the
current MAX(id) of its table. It is idempotent and PostgreSQL-only; on SQLite
(used by the test suite) it is a no-op.

Revision ID: v20260704_reset_sequences
Revises: w20260601_accepted
Create Date: 2026-07-04
"""

from __future__ import annotations

from alembic import op

revision: str = "v20260704_reset_sequences"
down_revision: str | None = "w20260601_accepted"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite (tests) uses AUTOINCREMENT rowids; nothing to realign.
        return

    # Realign every serial-backed column in the public schema to MAX(value).
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN
                SELECT
                    c.table_name,
                    c.column_name,
                    pg_get_serial_sequence(
                        quote_ident(c.table_schema) || '.' || quote_ident(c.table_name),
                        c.column_name
                    ) AS seq
                FROM information_schema.columns c
                WHERE c.table_schema = 'public'
                  AND c.column_default LIKE 'nextval(%'
            LOOP
                IF r.seq IS NOT NULL THEN
                    EXECUTE format(
                        'SELECT setval(%L, COALESCE((SELECT MAX(%I) FROM %I), 1))',
                        r.seq, r.column_name, r.table_name
                    );
                END IF;
            END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    # Realigning sequences is not reversible in a meaningful way.
    pass
