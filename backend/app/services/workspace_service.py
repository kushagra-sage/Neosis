"""Workspace service — CRUD with ownership enforcement."""

from __future__ import annotations

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inquiry import Inquiry
from app.db.models.library import Note, Paper
from app.db.models.research import (
    Experiment,
    FutureIdea,
    LiteratureReview,
    ResearchGap,
    ResearchQuestion,
)
from app.db.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceStatsResponse,
    WorkspaceUpdate,
)


async def _unique_slug(db: AsyncSession, user_id: str, base: str) -> str:
    """Return a slug that is unique within this user's workspaces."""
    slug = slugify(base, max_length=180, word_boundary=True)
    candidate = slug
    counter = 1
    while True:
        existing = await db.execute(
            select(Workspace).where(
                Workspace.user_id == user_id, Workspace.slug == candidate
            )
        )
        if existing.scalar_one_or_none() is None:
            return candidate
        candidate = f"{slug}-{counter}"
        counter += 1


async def create_workspace(
    db: AsyncSession, user_id: str, body: WorkspaceCreate
) -> Workspace:
    slug = await _unique_slug(db, user_id, body.name)
    ws = Workspace(
        user_id=user_id,
        name=body.name,
        slug=slug,
        domain=body.domain,
        description=body.description,
    )
    db.add(ws)
    await db.flush()
    return ws


async def list_workspaces(db: AsyncSession, user_id: str) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .where(Workspace.user_id == user_id)
        .order_by(Workspace.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_workspace(
    db: AsyncSession, workspace_id: str, user_id: str
) -> Workspace:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.user_id == user_id
        )
    )
    ws = result.scalar_one_or_none()
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


async def update_workspace(
    db: AsyncSession, workspace_id: str, user_id: str, body: WorkspaceUpdate
) -> Workspace:
    ws = await get_workspace(db, workspace_id, user_id)
    if body.name is not None:
        ws.name = body.name
        ws.slug = await _unique_slug(db, user_id, body.name)
    if body.description is not None:
        ws.description = body.description
    await db.flush()
    return ws


async def delete_workspace(
    db: AsyncSession, workspace_id: str, user_id: str
) -> None:
    ws = await get_workspace(db, workspace_id, user_id)
    await db.delete(ws)
    await db.flush()


async def workspace_stats(
    db: AsyncSession, workspace_id: str, user_id: str
) -> WorkspaceStatsResponse:
    # Verify ownership first.
    await get_workspace(db, workspace_id, user_id)

    async def _count(model, col):  # type: ignore[type-arg]
        r = await db.execute(
            select(func.count()).select_from(model).where(col == workspace_id)
        )
        return r.scalar_one()

    return WorkspaceStatsResponse(
        papers=await _count(Paper, Paper.workspace_id),
        notes=await _count(Note, Note.workspace_id),
        questions=await _count(ResearchQuestion, ResearchQuestion.workspace_id),
        experiments=await _count(Experiment, Experiment.workspace_id),
        reviews=await _count(LiteratureReview, LiteratureReview.workspace_id),
        gaps=await _count(ResearchGap, ResearchGap.workspace_id),
        ideas=await _count(FutureIdea, FutureIdea.workspace_id),
        inquiries=await _count(Inquiry, Inquiry.workspace_id),
    )
