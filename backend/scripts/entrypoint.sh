#!/usr/bin/env bash
set -euo pipefail

# Production-safe startup: Alembic is the single source of truth for the schema.
# Run migrations to head, then start the API. If a migration fails, the
# container exits non-zero and never serves a half-migrated schema.

echo "[entrypoint] running database migrations (alembic upgrade head)…"
alembic upgrade head

echo "[entrypoint] migrations complete; starting API…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
