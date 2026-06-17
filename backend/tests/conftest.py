"""Shared test fixtures — SQLite in-memory, no live infra required."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.config import settings
from fastapi import FastAPI
from app.api.router import api_router


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture()
async def auth_tokens(client: AsyncClient) -> dict:
    await client.post(f"{settings.api_v1_prefix}/auth/register", json={
        "username": "testuser", "email": "test@example.com", "password": "testpass123"
    })
    resp = await client.post(
        f"{settings.api_v1_prefix}/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    return resp.json()


@pytest_asyncio.fixture()
async def auth_header(auth_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}
