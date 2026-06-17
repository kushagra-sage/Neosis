"""Workspace endpoint tests — CRUD, ownership, presets."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings

PREFIX = settings.api_v1_prefix


@pytest.mark.asyncio
async def test_list_workspaces_empty(client: AsyncClient, auth_header: dict) -> None:
    resp = await client.get(f"{PREFIX}/workspaces", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient, auth_header: dict) -> None:
    resp = await client.post(
        f"{PREFIX}/workspaces",
        headers=auth_header,
        json={"name": "RA Severity Research", "domain": "ra_severity"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "RA Severity Research"
    assert body["domain"] == "ra_severity"
    assert "slug" in body
    assert "id" in body


@pytest.mark.asyncio
async def test_get_workspace(client: AsyncClient, auth_header: dict) -> None:
    create = await client.post(
        f"{PREFIX}/workspaces",
        headers=auth_header,
        json={"name": "Patent Research", "domain": "patent"},
    )
    ws_id = create.json()["id"]

    resp = await client.get(f"{PREFIX}/workspaces/{ws_id}", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["id"] == ws_id


@pytest.mark.asyncio
async def test_update_workspace(client: AsyncClient, auth_header: dict) -> None:
    create = await client.post(
        f"{PREFIX}/workspaces",
        headers=auth_header,
        json={"name": "Old Name", "domain": "custom"},
    )
    ws_id = create.json()["id"]

    resp = await client.patch(
        f"{PREFIX}/workspaces/{ws_id}",
        headers=auth_header,
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_workspace(client: AsyncClient, auth_header: dict) -> None:
    create = await client.post(
        f"{PREFIX}/workspaces",
        headers=auth_header,
        json={"name": "To Delete"},
    )
    ws_id = create.json()["id"]

    resp = await client.delete(f"{PREFIX}/workspaces/{ws_id}", headers=auth_header)
    assert resp.status_code == 200

    resp2 = await client.get(f"{PREFIX}/workspaces/{ws_id}", headers=auth_header)
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_workspace_not_found_for_other_user(client: AsyncClient, db_session) -> None:
    from app.config import settings as cfg
    # Register two users
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "user1", "email": "u1@ex.com", "password": "pass1234"
    })
    await client.post(f"{PREFIX}/auth/register", json={
        "username": "user2", "email": "u2@ex.com", "password": "pass5678"
    })

    resp1 = await client.post(f"{PREFIX}/auth/login", data={"username": "user1", "password": "pass1234"})
    token1 = resp1.json()["access_token"]
    resp2 = await client.post(f"{PREFIX}/auth/login", data={"username": "user2", "password": "pass5678"})
    token2 = resp2.json()["access_token"]

    ws_resp = await client.post(
        f"{PREFIX}/workspaces",
        headers={"Authorization": f"Bearer {token1}"},
        json={"name": "User1 WS"},
    )
    ws_id = ws_resp.json()["id"]

    # user2 should not be able to access user1's workspace
    resp = await client.get(
        f"{PREFIX}/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_stats(client: AsyncClient, auth_header: dict) -> None:
    create = await client.post(
        f"{PREFIX}/workspaces", headers=auth_header, json={"name": "Stats WS"}
    )
    ws_id = create.json()["id"]

    resp = await client.get(f"{PREFIX}/workspaces/{ws_id}/stats", headers=auth_header)
    assert resp.status_code == 200
    body = resp.json()
    assert body["papers"] == 0
    assert body["reviews"] == 0


@pytest.mark.asyncio
async def test_list_presets(client: AsyncClient) -> None:
    resp = await client.get(f"{PREFIX}/workspaces/presets")
    assert resp.status_code == 200
    presets = resp.json()
    keys = [p["key"] for p in presets]
    assert "ra_severity" in keys
    assert "patent" in keys


@pytest.mark.asyncio
async def test_create_from_preset(client: AsyncClient, auth_header: dict) -> None:
    resp = await client.post(
        f"{PREFIX}/workspaces/from-preset/ra_severity", headers=auth_header
    )
    assert resp.status_code == 201
    assert resp.json()["domain"] == "ra_severity"


@pytest.mark.asyncio
async def test_slug_uniqueness(client: AsyncClient, auth_header: dict) -> None:
    await client.post(f"{PREFIX}/workspaces", headers=auth_header, json={"name": "My Research"})
    resp2 = await client.post(f"{PREFIX}/workspaces", headers=auth_header, json={"name": "My Research"})
    assert resp2.status_code == 201
    # Second workspace gets a suffixed slug
    assert resp2.json()["slug"] != "my-research"
