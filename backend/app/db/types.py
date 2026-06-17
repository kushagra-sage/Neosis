"""Portable JSON column type.

Uses PostgreSQL ``JSONB`` in production (indexable, binary) and falls back to
the generic ``JSON`` type on SQLite so the same models work in the test suite.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSONB().with_variant(JSON(), "sqlite")
