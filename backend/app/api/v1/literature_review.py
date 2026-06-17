"""Literature Review mode endpoints (workspace-scoped).

  POST   /workspaces/{id}/reviews          — generate a new literature review
  GET    /workspaces/{id}/reviews          — list reviews
  GET    /workspaces/{id}/reviews/{rid}    — review detail
  DELETE /workspaces/{id}/reviews/{rid}    — delete a review
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.literature_review import (
    LiteratureReviewListItem,
    LiteratureReviewRequest,
    LiteratureReviewResponse,
)
from app.security.dependencies import CurrentUser
from app.services import literature_review_service as svc
from app.services.workspace_service import get_workspace

router = APIRouter(prefix="/workspaces/{workspace_id}/reviews", tags=["literature-review"])


@router.post("", response_model=LiteratureReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    workspace_id: str,
    body: LiteratureReviewRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiteratureReviewResponse:
    await get_workspace(db, workspace_id, current_user.id)  # ownership check
    review = await svc.generate_literature_review(
        db,
        workspace_id=workspace_id,
        topic=body.topic,
        user_id=current_user.id,
    )
    await db.commit()
    await db.refresh(review)
    return LiteratureReviewResponse.model_validate(review)


@router.get("", response_model=list[LiteratureReviewListItem])
async def list_reviews(
    workspace_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LiteratureReviewListItem]:
    await get_workspace(db, workspace_id, current_user.id)
    reviews = await svc.list_reviews(db, workspace_id=workspace_id)
    return [LiteratureReviewListItem.model_validate(r) for r in reviews]


@router.get("/{review_id}", response_model=LiteratureReviewResponse)
async def get_review(
    workspace_id: str,
    review_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiteratureReviewResponse:
    await get_workspace(db, workspace_id, current_user.id)
    review = await svc.get_review(db, review_id=review_id, workspace_id=workspace_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Literature review not found")
    return LiteratureReviewResponse.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    workspace_id: str,
    review_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await get_workspace(db, workspace_id, current_user.id)
    review = await svc.get_review(db, review_id=review_id, workspace_id=workspace_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Literature review not found")
    await svc.delete_review(db, review=review)
    await db.commit()
    return {"detail": "deleted"}
