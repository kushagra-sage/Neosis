"""repair users.display_name and users.last_active_at (idempotent)

Revision ID: 0003
Revises: 0002

Repairs a drift where the database is stamped at 0002 but the two user columns
added in 0002 (``display_name``, ``last_active_at``) are missing — typically
because the documents/chunks/reset tables were pre-created by a dev-mode
``create_all()`` and the 0002 column additions never applied cleanly.

This migration introspects the live schema and only adds each column if it is
absent, so it is safe to run on:
  * a drifted database (columns missing)        -> columns added
  * a correct database (columns already present) -> no-op
  * a fresh install (0001 -> 0002 -> 0003)       -> no-op (0002 already added them)

PostgreSQL-compatible and idempotent. Does not modify any prior migration.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _existing_columns(table: str) -> set[str]:
    """Return the set of column names currently present on *table*."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    columns = _existing_columns("users")

    # users.display_name — nullable VARCHAR(120)
    if "display_name" not in columns:
        op.add_column(
            "users",
            sa.Column("display_name", sa.String(length=120), nullable=True),
        )

    # users.last_active_at — nullable timestamptz (activity tracking / DAU-WAU-MAU)
    if "last_active_at" not in columns:
        op.add_column(
            "users",
            sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    # Only drop what is present, so a partial state downgrades cleanly too.
    columns = _existing_columns("users")

    if "last_active_at" in columns:
        op.drop_column("users", "last_active_at")
    if "display_name" in columns:
        op.drop_column("users", "display_name")
