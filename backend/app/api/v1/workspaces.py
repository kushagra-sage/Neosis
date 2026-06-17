"""Workspace routes.

  GET    /workspaces                   — list the authenticated user's workspaces
  POST   /workspaces                   — create a workspace
  GET    /workspaces/presets           — list quick-start templates
  POST   /workspaces/from-preset/{key} — create a workspace from a preset
  GET    /workspaces/{id}              — get a single workspace
  PATCH  /workspaces/{id}              — update name / description
  DELETE /workspaces/{id}              — delete
  GET    /workspaces/{id}/stats        — paper/review/gap counts
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.workspace import (
    WORKSPACE_PRESETS,
    PresetResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceStatsResponse,
    WorkspaceUpdate,
)
from app.security.dependencies import CurrentUser
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[WorkspaceResponse]:
    workspaces = await workspace_service.list_workspaces(db, current_user.id)
    return [WorkspaceResponse.model_validate(ws) for ws in workspaces]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    ws = await workspace_service.create_workspace(db, current_user.id, body)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.get("/presets", response_model=list[PresetResponse])
async def list_presets() -> list[PresetResponse]:
    return [
        PresetResponse(key=k, name=v["name"], domain=v["domain"], description=v["description"])
        for k, v in WORKSPACE_PRESETS.items()
    ]


@router.post(
    "/from-preset/{preset_key}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_from_preset(
    preset_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    if preset_key not in WORKSPACE_PRESETS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    preset = WORKSPACE_PRESETS[preset_key]
    body = WorkspaceCreate(
        name=preset["name"],
        domain=preset["domain"],
        description=preset["description"],
    )
    ws = await workspace_service.create_workspace(db, current_user.id, body)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    ws = await workspace_service.get_workspace(db, workspace_id, current_user.id)
    return WorkspaceResponse.model_validate(ws)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    body: WorkspaceUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    ws = await workspace_service.update_workspace(db, workspace_id, current_user.id, body)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
async def delete_workspace(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await workspace_service.delete_workspace(db, workspace_id, current_user.id)
    await db.commit()
    return {"detail": "deleted"}


@router.get("/{workspace_id}/stats", response_model=WorkspaceStatsResponse)
async def workspace_stats(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceStatsResponse:
    return await workspace_service.workspace_stats(db, workspace_id, current_user.id)
