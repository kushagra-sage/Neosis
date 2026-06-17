"""Library routes — manage papers and notes in a workspace."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.library import Note, Paper
from app.db.session import get_db
from app.schemas.library import NoteCreate, NoteResponse, PaperImportRequest, PaperResponse
from app.security.dependencies import CurrentUser
from app.services.workspace_service import get_workspace

router = APIRouter(prefix="/workspaces/{workspace_id}/library", tags=["library"])


@router.post("/papers", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
async def import_paper(
    workspace_id: str,
    body: PaperImportRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaperResponse:
    await get_workspace(db, workspace_id, current_user.id)  # ownership check
    paper = Paper(
        workspace_id=workspace_id,
        title=body.title,
        authors=body.authors,
        year=body.year,
        venue=body.venue,
        abstract=body.abstract,
        source=body.source,
        external_id=body.external_id,
        doi=body.doi,
        arxiv_id=body.arxiv_id,
        url=body.url,
        citation_count=body.citation_count,
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return PaperResponse.model_validate(paper)


@router.get("/papers", response_model=list[PaperResponse])
async def list_papers(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PaperResponse]:
    await get_workspace(db, workspace_id, current_user.id)
    result = await db.execute(
        select(Paper)
        .where(Paper.workspace_id == workspace_id)
        .order_by(Paper.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [PaperResponse.model_validate(p) for p in result.scalars().all()]


@router.delete("/papers/{paper_id}", status_code=status.HTTP_200_OK)
async def delete_paper(
    workspace_id: str,
    paper_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await get_workspace(db, workspace_id, current_user.id)
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.workspace_id == workspace_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    await db.delete(paper)
    await db.commit()


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    workspace_id: str,
    body: NoteCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteResponse:
    await get_workspace(db, workspace_id, current_user.id)
    note = Note(
        workspace_id=workspace_id,
        paper_id=body.paper_id,
        title=body.title,
        body=body.body,
        tags=body.tags,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get("/notes", response_model=list[NoteResponse])
async def list_notes(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[NoteResponse]:
    await get_workspace(db, workspace_id, current_user.id)
    result = await db.execute(
        select(Note)
        .where(Note.workspace_id == workspace_id)
        .order_by(Note.created_at.desc())
    )
    return [NoteResponse.model_validate(n) for n in result.scalars().all()]
