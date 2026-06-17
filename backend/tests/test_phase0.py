"""Phase 0 smoke tests — no live infrastructure required."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.config import Settings, settings
from app.db.models import User, Workspace
from app.db.models.enums import WorkspaceDomain


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.api_v1_prefix}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "Noesis"


@pytest.mark.asyncio
async def test_version(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.api_v1_prefix}/version")
    assert resp.status_code == 200
    assert "version" in resp.json()


def test_database_url_built_from_parts() -> None:
    s = Settings(
        postgres_user="u",
        postgres_password="p",
        postgres_host="h",
        postgres_port=5432,
        postgres_db="d",
    )
    assert s.database_url == "postgresql+asyncpg://u:p@h:5432/d"
    assert s.database_url_sync == "postgresql+psycopg://u:p@h:5432/d"


def test_cors_origins_parsed() -> None:
    s = Settings(cors_origins="http://a.com, http://b.com")
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


@pytest.mark.asyncio
async def test_schema_creates_and_relationships_work(db_session) -> None:
    """All tables create on SQLite and a workspace links to its owner."""
    user = User(username="amit", email="amit@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.flush()

    ws = Workspace(
        user_id=user.id,
        name="RA Severity Research",
        slug="ra-severity-research",
        domain=WorkspaceDomain.RA_SEVERITY,
    )
    db_session.add(ws)
    await db_session.commit()

    result = await db_session.execute(select(Workspace).where(Workspace.user_id == user.id))
    fetched = result.scalar_one()
    assert fetched.name == "RA Severity Research"
    assert fetched.domain is WorkspaceDomain.RA_SEVERITY
