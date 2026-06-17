"""Document upload + knowledge-base management.

  POST   /documents/upload        — multipart upload (pdf/docx/txt/markdown)
  GET    /documents               — list the caller's documents
  GET    /documents/{id}          — document detail
  DELETE /documents/{id}          — remove document + vectors + original
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.document import DocumentListItem, DocumentResponse
from app.security.dependencies import CurrentUser
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
    workspace_id: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    filename = file.filename or "untitled"
    if document_service.detect_kind(filename) is None:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Allowed: PDF, DOCX, TXT, Markdown.",
        )

    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit.")

    doc = await document_service.create_document(
        db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        filename=filename,
        data=data,
    )
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: str | None = None,
) -> list[DocumentListItem]:
    docs = await document_service.list_documents(
        db, user_id=current_user.id, workspace_id=workspace_id
    )
    return [DocumentListItem.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentResponse:
    doc = await document_service.get_document(
        db, document_id=document_id, user_id=current_user.id
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    doc = await document_service.get_document(
        db, document_id=document_id, user_id=current_user.id
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await document_service.delete_document(db, document=doc)
    await db.commit()
    return {"detail": "deleted"}
