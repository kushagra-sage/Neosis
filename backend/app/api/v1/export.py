"""Export system endpoints.

  GET /export/inquiry/{id}?format=pdf|docx|markdown|bibtex
  GET /workspaces/{ws}/reviews/{rid}/export?format=...

Streams a downloadable file. Citations are preserved in every format.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.security.dependencies import CurrentUser
from app.services import export_service
from app.services.inquiry_service import get_inquiry
from app.services.literature_review_service import get_review
from app.services.workspace_service import get_workspace

router = APIRouter(tags=["export"])

_FORMATS = {"markdown", "bibtex", "docx", "pdf"}


def _validate(fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in _FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Use one of: {', '.join(sorted(_FORMATS))}.",
        )
    return fmt


def _file_response(data: bytes, mime: str, filename: str) -> Response:
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/inquiry/{inquiry_id}")
async def export_inquiry(
    inquiry_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query(default="pdf"),
) -> Response:
    fmt = _validate(format)
    inquiry = await get_inquiry(db, inquiry_id, current_user.id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    citations = list(inquiry.dossier or [])
    # Normalise dossier items into the citation shape the exporter expects.
    norm = [
        {
            "title": c.get("title"),
            "authors": c.get("authors"),
            "year": c.get("year"),
            "venue": c.get("venue"),
            "source": c.get("source"),
            "url": c.get("url"),
            "doi": c.get("doi"),
            "arxiv_id": c.get("arxiv_id"),
        }
        for c in citations
    ]

    doc = export_service.ExportDocument(
        title=inquiry.question[:120],
        subtitle="Noesis research answer",
        body_markdown=inquiry.answer or "_No answer recorded._",
        citations=norm,
        meta={"inquiry_id": inquiry.id},
    )
    data, mime, filename = export_service.render(doc, fmt)
    return _file_response(data, mime, filename)


@router.get("/workspaces/{workspace_id}/reviews/{review_id}/export")
async def export_review(
    workspace_id: str,
    review_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query(default="pdf"),
) -> Response:
    fmt = _validate(format)
    await get_workspace(db, workspace_id, current_user.id)
    review = await get_review(db, review_id=review_id, workspace_id=workspace_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Literature review not found")

    doc = export_service.ExportDocument(
        title=review.title,
        subtitle="Noesis literature review",
        body_markdown=review.content,
        citations=list(review.citations or []),
        meta={"review_id": review.id},
    )
    data, mime, filename = export_service.render(doc, fmt)
    return _file_response(data, mime, filename)
