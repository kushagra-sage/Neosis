"""Auth endpoint tests — full JWT flow, refresh rotation, stats."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings

PREFIX = settings.api_v1_prefix


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post(f"{PREFIX}/auth/register", json={
        "username": "amit", "email": "amit@example.com", "password": "securepass1"
    })
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    payload = {"username": "dup", "email": "dup@example.com", "password": "securepass1"}
    await client.post(f"{PREFIX}/auth/register", json=payload)
    resp = await client.post(f"{PREFIX}/auth/register", json={**payload, "email": "dup2@ex.com"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "userA", "email": "shared@ex.com", "password": "pass1234"
    })
    resp = await client.post(f"{PREFIX}/auth/register", json={
        "username": "userB", "email": "shared@ex.com", "password": "pass1234"
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_with_username(client: AsyncClient) -> None:
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "loginuser", "email": "login@example.com", "password": "pass1234"
    })
    resp = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "loginuser", "password": "pass1234"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_with_email(client: AsyncClient) -> None:
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "emaillogin", "email": "emaillogin@example.com", "password": "pass5678"
    })
    resp = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "emaillogin@example.com", "password": "pass5678"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "wpuser", "email": "wp@example.com", "password": "correct1"
    })
    resp = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "wpuser", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_header: dict) -> None:
    resp = await client.get(f"{PREFIX}/auth/me", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient) -> None:
    resp = await client.get(f"{PREFIX}/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotation(client: AsyncClient, auth_tokens: dict) -> None:
    resp = await client.post(
        f"{PREFIX}/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    # Refresh tokens must rotate (different jti)
    assert new_tokens["refresh_token"] != auth_tokens["refresh_token"]
    # New tokens must be valid JWTs
    assert new_tokens["access_token"].startswith("eyJ")

    # Old refresh token should now be revoked
    resp2 = await client.post(
        f"{PREFIX}/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_tokens: dict) -> None:
    resp = await client.post(
        f"{PREFIX}/auth/logout",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_me_stats(client: AsyncClient, auth_header: dict) -> None:
    resp = await client.get(f"{PREFIX}/auth/me/stats", headers=auth_header)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_workspaces" in body
    assert body["total_workspaces"] == 0
